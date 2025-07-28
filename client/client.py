#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Client léger pour le système de pentesting éthique automatisé
Ce script doit être exécuté avec des privilèges administrateur/root sur la machine cible.
"""

import os
import sys
import socket
import uuid
import platform
import json
import argparse
import requests
import subprocess
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pentesting_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PentestClient")

class PentestClient:
    def __init__(self, api_url, token=None):
        """
        Initialise le client de pentesting
        
        Args:
            api_url (str): URL de l'API de pentesting
            token (str, optional): Token d'authentification
        """
        self.api_url = api_url
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.system_info = {}
        
        # Vérification des privilèges
        if not self._check_privileges():
            logger.error("Ce script doit être exécuté avec des privilèges administrateur/root")
            sys.exit(1)
            
        logger.info(f"Client initialisé avec l'API: {api_url}")
    
    def _check_privileges(self):
        """Vérifie si le script est exécuté avec des privilèges administrateur/root"""
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:  # Unix/Linux/MacOS
                return os.geteuid() == 0
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des privilèges: {e}")
            return False
    
    def collect_system_info(self):
        """Collecte les informations système demandées"""
        logger.info("Collecte des informations système...")
        
        try:
            # Système d'exploitation
            self.system_info["os"] = platform.system()
            self.system_info["os_version"] = platform.version()
            self.system_info["os_release"] = platform.release()
            
            # Nom d'hôte
            self.system_info["hostname"] = socket.gethostname()
            
            # Adresse IP locale
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Ne se connecte pas réellement, juste pour obtenir l'interface par défaut
                s.connect(("8.8.8.8", 80))
                self.system_info["local_ip"] = s.getsockname()[0]
            except Exception as e:
                logger.warning(f"Impossible de déterminer l'IP locale: {e}")
                self.system_info["local_ip"] = "Inconnue"
            finally:
                s.close()
            
            # Adresse MAC
            if os.name == 'nt':  # Windows
                from uuid import getnode
                mac = ':'.join(['{:02x}'.format((getnode() >> elements) & 0xff) for elements in range(0, 8*6, 8)][::-1])
                self.system_info["mac_address"] = mac
            else:  # Unix/Linux/MacOS
                try:
                    import netifaces
                    interfaces = netifaces.interfaces()
                    for interface in interfaces:
                        if interface != 'lo':  # Ignorer l'interface loopback
                            try:
                                mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
                                if mac:
                                    self.system_info["mac_address"] = mac
                                    break
                            except:
                                pass
                except ImportError:
                    # Fallback si netifaces n'est pas disponible
                    try:
                        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 8*6, 8)][::-1])
                        self.system_info["mac_address"] = mac
                    except:
                        self.system_info["mac_address"] = "Inconnue"
            
            # DNS
            try:
                dns_servers = []
                if os.name == 'nt':  # Windows
                    output = subprocess.check_output("ipconfig /all", shell=True).decode('utf-8')
                    for line in output.split('\n'):
                        if "DNS Servers" in line or "Serveurs DNS" in line:
                            dns_line = line.split(':')[-1].strip()
                            if dns_line and not dns_line.startswith("fec0"):
                                dns_servers.append(dns_line)
                else:  # Unix/Linux/MacOS
                    with open('/etc/resolv.conf', 'r') as f:
                        for line in f:
                            if line.startswith('nameserver'):
                                dns_servers.append(line.split()[1])
                
                self.system_info["dns_servers"] = dns_servers if dns_servers else ["Inconnus"]
            except Exception as e:
                logger.warning(f"Impossible de déterminer les serveurs DNS: {e}")
                self.system_info["dns_servers"] = ["Inconnus"]
            
            # Date et heure de la collecte
            self.system_info["collection_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info("Informations système collectées avec succès")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des informations système: {e}")
            return False
    
    def display_authorization(self):
        """Affiche le document d'autorisation et demande la confirmation de l'utilisateur"""
        authorization_text = """
        ========== AUTORISATION DE TEST DE PÉNÉTRATION ÉTHIQUE ==========
        
        En acceptant ce document, vous autorisez l'exécution d'un test de pénétration
        éthique automatisé sur cette machine uniquement. Ce test inclut:
        
        1. La collecte d'informations système
        2. L'énumération des services et ports
        3. La recherche de vulnérabilités
        4. La vérification de vulnérabilités (sans exploitation destructive)
        5. La génération d'un rapport détaillé
        
        IMPORTANT:
        - Ce test est limité à cette machine uniquement
        - Aucune donnée ne sera modifiée ou supprimée
        - Un rapport complet sera généré à la fin du test
        - Vous pouvez interrompre le test à tout moment avec Ctrl+C
        
        En acceptant, vous confirmez avoir l'autorité légale pour autoriser
        ce test sur cette machine.
        
        ================================================================
        """
        
        print(authorization_text)
        
        while True:
            response = input("Acceptez-vous de procéder au test de pénétration éthique? (oui/non): ").lower()
            if response in ['oui', 'o', 'yes', 'y']:
                logger.info("Autorisation acceptée par l'utilisateur")
                return True
            elif response in ['non', 'n', 'no']:
                logger.info("Autorisation refusée par l'utilisateur")
                return False
            else:
                print("Veuillez répondre par 'oui' ou 'non'")
    
    def connect_to_api(self):
        """Établit la connexion avec l'API et obtient un token d'authentification"""
        try:
            logger.info(f"Tentative de connexion à l'API: {self.api_url}")
            
            response = requests.post(
                f"{self.api_url}/auth/client",
                json={"system_info": self.system_info},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                logger.info("Connexion à l'API établie avec succès")
                return True
            else:
                logger.error(f"Échec de la connexion à l'API: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion à l'API: {e}")
            return False
    
    def execute_command(self, command):
        """Exécute une commande système et retourne le résultat"""
        try:
            logger.info(f"Exécution de la commande: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
            return output
        
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la commande: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": 1
            }
    
    def send_command_result(self, command_id, result):
        """Envoie le résultat d'une commande à l'API"""
        try:
            response = requests.post(
                f"{self.api_url}/scan/result/{command_id}",
                headers=self.headers,
                json=result,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Résultat de la commande {command_id} envoyé avec succès")
                return True
            else:
                logger.error(f"Échec de l'envoi du résultat: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de l'envoi du résultat: {e}")
            return False
    
    def get_next_command(self):
        """Récupère la prochaine commande à exécuter depuis l'API"""
        try:
            response = requests.get(
                f"{self.api_url}/scan/next_command",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data
            elif response.status_code == 204:
                logger.info("Aucune commande à exécuter pour le moment")
                return None
            else:
                logger.error(f"Échec de la récupération de commande: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération de commande: {e}")
            return None
    
    def get_scan_status(self):
        """Récupère le statut du scan en cours"""
        try:
            response = requests.get(
                f"{self.api_url}/scan/status",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"Échec de la récupération du statut: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            return None
    
    def get_final_report(self, format="pdf"):
        """Récupère le rapport final du scan"""
        try:
            response = requests.get(
                f"{self.api_url}/report/final?format={format}",
                headers=self.headers,
                timeout=30,
                stream=True
            )
            
            if response.status_code == 200:
                # Déterminer le nom du fichier
                filename = f"rapport_pentest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
                
                # Enregistrer le rapport
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Rapport final téléchargé: {filename}")
                return filename
            else:
                logger.error(f"Échec du téléchargement du rapport: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors du téléchargement du rapport: {e}")
            return None
    
    def run_scan(self):
        """Exécute le processus complet de scan"""
        try:
            # Afficher le document d'autorisation
            if not self.display_authorization():
                logger.info("Scan annulé par l'utilisateur")
                return False
            
            # Collecter les informations système
            if not self.collect_system_info():
                logger.error("Impossible de collecter les informations système")
                return False
            
            # Se connecter à l'API
            if not self.connect_to_api():
                logger.error("Impossible de se connecter à l'API")
                return False
            
            # Boucle principale d'exécution des commandes
            print("\nDémarrage du scan de pentesting...\n")
            
            while True:
                # Vérifier le statut du scan
                status = self.get_scan_status()
                
                if status and status.get("status") == "completed":
                    logger.info("Scan terminé avec succès")
                    break
                
                # Récupérer la prochaine commande
                command_data = self.get_next_command()
                
                if not command_data:
                    # Attendre un peu avant de redemander une commande
                    import time
                    time.sleep(5)
                    continue
                
                command_id = command_data.get("id")
                command = command_data.get("command")
                
                # Exécuter la commande
                result = self.execute_command(command)
                
                # Envoyer le résultat
                self.send_command_result(command_id, result)
            
            # Télécharger le rapport final
            print("\nScan terminé. Téléchargement du rapport final...\n")
            
            # Demander le format du rapport
            while True:
                format_choice = input("Dans quel format souhaitez-vous le rapport? (pdf/html): ").lower()
                if format_choice in ['pdf', 'html']:
                    break
                else:
                    print("Format non valide. Veuillez choisir 'pdf' ou 'html'.")
            
            report_file = self.get_final_report(format=format_choice)
            
            if report_file:
                print(f"\nRapport téléchargé avec succès: {report_file}\n")
                return True
            else:
                logger.error("Échec du téléchargement du rapport final")
                return False
                
        except KeyboardInterrupt:
            logger.info("Scan interrompu par l'utilisateur")
            print("\nScan interrompu. Nettoyage en cours...\n")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du scan: {e}")
            return False


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Client de pentesting éthique automatisé")
    parser.add_argument("--api", required=True, help="URL de l'API de pentesting")
    parser.add_argument("--token", help="Token d'authentification (optionnel)")
    
    args = parser.parse_args()
    
    client = PentestClient(args.api, args.token)
    success = client.run_scan()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
