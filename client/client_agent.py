#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Client Agent pour le système de pentesting éthique automatisé (Refactorisé avec WebSocket)
Ce script doit être exécuté avec des privilèges administrateur/root sur la machine cible.
Communique avec l'API via WebSocket sécurisé (WSS).
"""

import os
import sys
import socket
import uuid
import platform
import json
import argparse
import subprocess
import logging
import asyncio
import websockets
import ssl
import pathlib
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pentesting_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PentestAgent")

# --- Configuration --- 
# Ces valeurs devraient idéalement provenir d'un fichier de config ou d'arguments
API_REST_URL = "http://localhost:80/api" # Pour l'enregistrement initial
API_WS_URL = "ws://localhost:80/ws" # URL WebSocket via Nginx (non-SSL pour l'instant)
# API_WS_URL_SECURE = "wss://your_domain.com/ws" # URL WebSocket sécurisée via Nginx

# Configuration mTLS (chemins vers les certificats)
# À générer et configurer correctement
# CERT_DIR = pathlib.Path(__file__).parent / "certs"
# CA_CERT = CERT_DIR / "ca.crt"
# CLIENT_CERT = CERT_DIR / "client.crt"
# CLIENT_KEY = CERT_DIR / "client.key"

CLIENT_UUID_FILE = "client_uuid.txt"

class PentestAgent:
    def __init__(self, api_rest_url, api_ws_url):
        """
        Initialise l'agent de pentesting
        
        Args:
            api_rest_url (str): URL de base de l'API REST (pour l'enregistrement)
            api_ws_url (str): URL de l'API WebSocket
        """
        self.api_rest_url = api_rest_url
        self.api_ws_url = api_ws_url
        self.system_info = {}
        self.client_uuid = self._load_or_generate_uuid()
        self.websocket = None
        self.is_running = True

        # Vérification des privilèges
        if not self._check_privileges():
            logger.error("Ce script doit être exécuté avec des privilèges administrateur/root")
            sys.exit(1)
            
        logger.info(f"Agent initialisé avec UUID: {self.client_uuid}")
        logger.info(f"API REST URL: {self.api_rest_url}")
        logger.info(f"API WS URL: {self.api_ws_url}")

    def _load_or_generate_uuid(self):
        """Charge l'UUID client depuis un fichier ou en génère un nouveau."""
        if os.path.exists(CLIENT_UUID_FILE):
            with open(CLIENT_UUID_FILE, 'r') as f:
                client_uuid = f.read().strip()
                if client_uuid:
                    logger.info(f"UUID client chargé: {client_uuid}")
                    return client_uuid
        
        client_uuid = str(uuid.uuid4())
        with open(CLIENT_UUID_FILE, 'w') as f:
            f.write(client_uuid)
        logger.info(f"Nouvel UUID client généré et sauvegardé: {client_uuid}")
        return client_uuid

    def _check_privileges(self):
        """Vérifie si le script est exécuté avec des privilèges administrateur/root"""
        try:
            if os.name == 'nt':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des privilèges: {e}")
            return False

    def collect_system_info(self):
        """Collecte les informations système de base."""
        logger.info("Collecte des informations système...")
        try:
            self.system_info["os"] = platform.system()
            self.system_info["os_version"] = platform.version()
            self.system_info["hostname"] = socket.gethostname()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                self.system_info["local_ip"] = s.getsockname()[0]
            except Exception:
                self.system_info["local_ip"] = "127.0.0.1"
            finally:
                s.close()

            # Utilisation de uuid.getnode() pour une approche multiplateforme simple
            mac_num = uuid.getnode()
            self.system_info["mac_address"] = ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))
            
            logger.info("Informations système collectées.")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des informations système: {e}")
            return False

    async def register_with_api(self):
        """Enregistre l'agent auprès de l'API REST."""
        if not self.collect_system_info():
            return False
        
        register_url = f"{self.api_rest_url}/clients/register"
        payload = {
            "hostname": self.system_info.get("hostname", "inconnu"),
            "os": self.system_info.get("os", "inconnu"),
            "local_ip": self.system_info.get("local_ip", "inconnu"),
            "mac_address": self.system_info.get("mac_address", "inconnu")
        }
        
        try:
            # Utilisation de requests pour la simplicité de l'enregistrement initial
            # Pourrait être remplacé par aiohttp si on veut tout en async
            import requests 
            logger.info(f"Enregistrement auprès de {register_url}...")
            response = requests.post(register_url, json=payload, timeout=10)
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP
            
            data = response.json()
            returned_uuid = data.get("client_uuid")
            
            if returned_uuid != self.client_uuid:
                logger.warning(f"L'UUID retourné par l'API ({returned_uuid}) diffère de l'UUID local ({self.client_uuid}). Mise à jour de l'UUID local.")
                self.client_uuid = returned_uuid
                with open(CLIENT_UUID_FILE, 'w') as f:
                    f.write(self.client_uuid)
            
            logger.info(f"Enregistrement réussi. UUID confirmé: {self.client_uuid}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Échec de l'enregistrement auprès de l'API: {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'enregistrement: {e}")
            return False

    def _get_ssl_context(self):
        """Crée le contexte SSL pour la connexion WebSocket mTLS."""
        # À décommenter et adapter lorsque les certificats sont prêts
        # if not all([CA_CERT.exists(), CLIENT_CERT.exists(), CLIENT_KEY.exists()]):
        #     logger.warning("Certificats mTLS non trouvés. Connexion non sécurisée (ws://).")
        #     return None # Connexion non sécurisée
        
        # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        # ssl_context.load_verify_locations(CA_CERT)
        # ssl_context.load_cert_chain(CLIENT_CERT, CLIENT_KEY)
        # ssl_context.check_hostname = False # Ou True si le nom d'hôte du serveur correspond au certificat
        # ssl_context.verify_mode = ssl.CERT_REQUIRED
        # logger.info("Contexte SSL mTLS configuré.")
        # return ssl_context
        
        # Pour l'instant, pas de SSL
        logger.warning("Configuration mTLS désactivée. Utilisation de ws://.")
        return None 

    async def send_message(self, message_type: str, payload: dict):
        """Envoie un message JSON structuré via WebSocket."""
        if self.websocket and self.websocket.open:
            message = {"type": message_type, "payload": payload}
            try:
                await self.websocket.send(json.dumps(message))
                logger.debug(f"Message envoyé: {message_type}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du message WebSocket: {e}")
        else:
            logger.warning("WebSocket non connecté. Impossible d'envoyer le message.")

    async def send_heartbeat(self):
        """Envoie un message heartbeat périodiquement."""
        while self.is_running:
            await asyncio.sleep(30) # Envoyer toutes les 30 secondes
            await self.send_message("heartbeat", {"timestamp": datetime.utcnow().isoformat()})

    def execute_command(self, command: str) -> dict:
        """Exécute une commande système et retourne le résultat."""
        logger.info(f"Exécution de la commande: {command}")
        try:
            # Utilisation de subprocess.run pour une meilleure gestion
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True, # Décode stdout/stderr en texte
                timeout=300 # Timeout de 5 minutes par commande
            )
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            logger.info(f"Commande terminée avec code: {result.returncode}")
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout lors de l'exécution de la commande: {command}")
            output = {"stdout": "", "stderr": "TimeoutExpired", "returncode": -1}
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la commande '{command}': {e}")
            output = {"stdout": "", "stderr": str(e), "returncode": -2}
        return output

    async def handle_command(self, task_uuid: str, command: str):
        """Exécute la commande reçue et renvoie le résultat."""
        result = self.execute_command(command)
        await self.send_message("command_result", {
            "task_uuid": task_uuid,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": result["returncode"]
        })

    async def listen_to_server(self):
        """Écoute les messages entrants du serveur WebSocket."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    payload = data.get("payload")
                    logger.debug(f"Message reçu: {message_type}")

                    if message_type == "command" and payload:
                        task_uuid = payload.get("task_uuid")
                        command_to_run = payload.get("command")
                        if task_uuid and command_to_run:
                            logger.info(f"Commande reçue (Task {task_uuid}): {command_to_run}")
                            # Exécuter la commande en arrière-plan pour ne pas bloquer l'écoute
                            asyncio.create_task(self.handle_command(task_uuid, command_to_run))
                        else:
                            logger.warning("Commande reçue invalide: {payload}")
                            
                    elif message_type == "scan_status" and payload:
                        logger.info(f"Mise à jour statut scan: {payload}")
                        # Afficher ou traiter le statut du scan
                        
                    elif message_type == "error" and payload:
                        logger.error(f"Erreur reçue de l'API: {payload.get('detail')}")
                        
                    # Gérer d'autres types de messages (pong, config update, etc.)
                    else:
                        logger.warning(f"Type de message inconnu reçu: {message_type}")
                        
                except json.JSONDecodeError:
                    logger.warning(f"Message WebSocket invalide (non-JSON): {message}")
                except Exception as e:
                    logger.error(f"Erreur lors du traitement du message WebSocket: {e}")
                    
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("Connexion WebSocket fermée proprement.")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connexion WebSocket fermée avec erreur: {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue dans la boucle d'écoute WebSocket: {e}")
        finally:
            self.is_running = False # Arrêter le heartbeat et la reconnexion

    async def run(self):
        """Fonction principale pour exécuter l'agent."""
        # 1. Enregistrement initial (synchrone pour la simplicité ici)
        if not await self.register_with_api():
             logger.error("Échec de l'enregistrement initial. Arrêt.")
             # Peut-être ajouter une logique de réessai ici
             return

        # 2. Boucle de connexion WebSocket
        ws_url = f"{self.api_ws_url}/{self.client_uuid}"
        ssl_context = self._get_ssl_context()
        
        while self.is_running:
            try:
                logger.info(f"Tentative de connexion à {ws_url}...")
                async with websockets.connect(ws_url, ssl=ssl_context, ping_interval=20, ping_timeout=20) as websocket:
                    self.websocket = websocket
                    logger.info("Connecté au serveur WebSocket.")
                    
                    # Lancer le heartbeat en tâche de fond
                    heartbeat_task = asyncio.create_task(self.send_heartbeat())
                    
                    # Écouter les messages du serveur
                    await self.listen_to_server()
                    
                    # Si listen_to_server se termine, annuler le heartbeat
                    heartbeat_task.cancel()
                    try:
                        await heartbeat_task
                    except asyncio.CancelledError:
                        logger.info("Tâche Heartbeat annulée.")
                        
            except (websockets.exceptions.InvalidURI,
                    websockets.exceptions.InvalidHandshake,
                    ConnectionRefusedError,
                    socket.gaierror,
                    OSError) as e:
                logger.error(f"Échec de la connexion WebSocket: {e}. Réessai dans 60 secondes...")
                self.websocket = None
            except Exception as e:
                logger.error(f"Erreur WebSocket inattendue: {e}. Réessai dans 60 secondes...")
                self.websocket = None
            
            if self.is_running: # Ne pas attendre si on a demandé l'arrêt
                await asyncio.sleep(60) # Attendre avant de retenter la connexion
            else:
                logger.info("Arrêt de la boucle de connexion.")
                break # Sortir de la boucle while
                
        logger.info("Agent arrêté.")

# --- Point d'entrée --- 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent de Pentesting CyberShield")
    parser.add_argument("--api-rest-url", default=API_REST_URL, help="URL de base de l'API REST")
    parser.add_argument("--api-ws-url", default=API_WS_URL, help="URL de l'API WebSocket")
    # Ajouter des arguments pour les chemins des certificats si mTLS est activé
    
    args = parser.parse_args()
    
    agent = PentestAgent(api_rest_url=args.api_rest_url, api_ws_url=args.api_ws_url)
    
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Interruption manuelle détectée. Arrêt de l'agent...")
        agent.is_running = False
        # Donner un peu de temps pour que les tâches s'arrêtent proprement
        # asyncio.sleep(1) 

