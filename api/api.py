#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API de pentesting pour le système de pentesting éthique automatisé
Cette API orchestre les tests de pénétration et communique avec le client léger.
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
import docker
import uuid
import json
import os
import logging
import time
from datetime import datetime, timedelta
import jwt
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pentesting_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PentestAPI")

# Configuration de l'API
app = FastAPI(
    title="API de Pentesting Éthique",
    description="API pour orchestrer des tests de pénétration éthiques automatisés",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration JWT
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", str(uuid.uuid4()))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 heures

# Client Docker
docker_client = docker.from_env()

# Répertoires de stockage
REPORTS_DIR = Path("./reports")
RESULTS_DIR = Path("./results")

# Création des répertoires s'ils n'existent pas
REPORTS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Modèles de données
class SystemInfo(BaseModel):
    system_info: Dict[str, Any]

class CommandResult(BaseModel):
    stdout: str
    stderr: str
    returncode: int

class ScanStatus(BaseModel):
    scan_id: str
    status: str
    progress: float
    current_phase: str
    start_time: str
    estimated_end_time: Optional[str] = None

# Stockage en mémoire (à remplacer par une base de données en production)
active_scans = {}
scan_results = {}
scan_commands = {}
scan_reports = {}

# Fonctions d'authentification
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_scan_id(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentification invalide")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        scan_id = payload.get("scan_id")
        if scan_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        if scan_id not in active_scans:
            raise HTTPException(status_code=404, detail="Scan non trouvé")
        
        return scan_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

# Routes de l'API
@app.get("/")
async def root():
    return {"message": "API de Pentesting Éthique Automatisé"}

@app.post("/auth/client")
async def authenticate_client(system_info: SystemInfo):
    """Authentifie un client et démarre un nouveau scan"""
    # Générer un ID unique pour ce scan
    scan_id = str(uuid.uuid4())
    
    # Enregistrer les informations système
    start_time = datetime.utcnow()
    
    active_scans[scan_id] = {
        "system_info": system_info.system_info,
        "status": "initializing",
        "progress": 0.0,
        "current_phase": "initialisation",
        "start_time": start_time.isoformat(),
        "commands": [],
        "results": {}
    }
    
    # Créer un répertoire pour les résultats de ce scan
    scan_dir = RESULTS_DIR / scan_id
    scan_dir.mkdir(exist_ok=True)
    
    # Sauvegarder les informations système
    with open(scan_dir / "system_info.json", "w") as f:
        json.dump(system_info.system_info, f, indent=2)
    
    # Générer un token d'accès
    access_token = create_access_token({"scan_id": scan_id})
    
    # Planifier les commandes initiales en arrière-plan
    background_tasks = BackgroundTasks()
    background_tasks.add_task(schedule_initial_commands, scan_id)
    
    logger.info(f"Nouveau scan initialisé: {scan_id}")
    
    return {"token": access_token, "scan_id": scan_id}

async def schedule_initial_commands(scan_id: str):
    """Planifie les commandes initiales pour un scan"""
    # Mettre à jour le statut
    active_scans[scan_id]["status"] = "running"
    active_scans[scan_id]["current_phase"] = "reconnaissance"
    
    # Ajouter les commandes de reconnaissance de base
    commands = [
        {
            "id": str(uuid.uuid4()),
            "command": "hostname -f",
            "phase": "reconnaissance",
            "description": "Obtenir le nom de domaine complet"
        },
        {
            "id": str(uuid.uuid4()),
            "command": "ip addr show",
            "phase": "reconnaissance",
            "description": "Obtenir les interfaces réseau et adresses IP"
        },
        {
            "id": str(uuid.uuid4()),
            "command": "cat /etc/resolv.conf",
            "phase": "reconnaissance",
            "description": "Obtenir la configuration DNS"
        }
    ]
    
    # Ajouter les commandes à la liste
    for cmd in commands:
        active_scans[scan_id]["commands"].append(cmd)
    
    logger.info(f"Commandes initiales planifiées pour le scan {scan_id}")

@app.get("/scan/next_command", status_code=200)
async def get_next_command(scan_id: str = Depends(get_current_scan_id)):
    """Récupère la prochaine commande à exécuter pour un scan"""
    # Vérifier s'il y a des commandes en attente
    pending_commands = [cmd for cmd in active_scans[scan_id]["commands"] 
                        if cmd["id"] not in active_scans[scan_id]["results"]]
    
    if not pending_commands:
        # Si toutes les commandes ont été exécutées, vérifier si nous devons passer à la phase suivante
        current_phase = active_scans[scan_id]["current_phase"]
        
        if current_phase == "reconnaissance":
            # Passer à la phase d'énumération
            active_scans[scan_id]["current_phase"] = "enumeration"
            active_scans[scan_id]["progress"] = 0.2
            
            # Planifier les commandes d'énumération
            await schedule_enumeration_commands(scan_id)
            
            # Récursion pour obtenir la prochaine commande
            return await get_next_command(scan_id)
            
        elif current_phase == "enumeration":
            # Passer à la phase de recherche de vulnérabilités
            active_scans[scan_id]["current_phase"] = "vulnerability_scanning"
            active_scans[scan_id]["progress"] = 0.4
            
            # Planifier les commandes de recherche de vulnérabilités
            await schedule_vulnerability_scanning_commands(scan_id)
            
            # Récursion pour obtenir la prochaine commande
            return await get_next_command(scan_id)
            
        elif current_phase == "vulnerability_scanning":
            # Passer à la phase d'exploitation
            active_scans[scan_id]["current_phase"] = "exploitation"
            active_scans[scan_id]["progress"] = 0.6
            
            # Planifier les commandes d'exploitation
            await schedule_exploitation_commands(scan_id)
            
            # Récursion pour obtenir la prochaine commande
            return await get_next_command(scan_id)
            
        elif current_phase == "exploitation":
            # Passer à la phase d'élévation de privilèges
            active_scans[scan_id]["current_phase"] = "privilege_escalation"
            active_scans[scan_id]["progress"] = 0.8
            
            # Planifier les commandes d'élévation de privilèges
            await schedule_privilege_escalation_commands(scan_id)
            
            # Récursion pour obtenir la prochaine commande
            return await get_next_command(scan_id)
            
        elif current_phase == "privilege_escalation":
            # Passer à la phase de nettoyage
            active_scans[scan_id]["current_phase"] = "cleanup"
            active_scans[scan_id]["progress"] = 0.9
            
            # Planifier les commandes de nettoyage
            await schedule_cleanup_commands(scan_id)
            
            # Récursion pour obtenir la prochaine commande
            return await get_next_command(scan_id)
            
        elif current_phase == "cleanup":
            # Terminer le scan
            active_scans[scan_id]["current_phase"] = "report_generation"
            active_scans[scan_id]["progress"] = 0.95
            
            # Générer le rapport en arrière-plan
            background_tasks = BackgroundTasks()
            background_tasks.add_task(generate_report, scan_id)
            
            # Pas de commande à retourner
            raise HTTPException(status_code=204, detail="Scan en cours de finalisation")
            
        elif current_phase == "report_generation":
            # Vérifier si le rapport est prêt
            if scan_id in scan_reports and scan_reports[scan_id]["status"] == "completed":
                active_scans[scan_id]["status"] = "completed"
                active_scans[scan_id]["progress"] = 1.0
            
            # Pas de commande à retourner
            raise HTTPException(status_code=204, detail="Génération du rapport en cours")
            
        else:
            # Pas de commande à retourner
            raise HTTPException(status_code=204, detail="Aucune commande disponible")
    
    # Retourner la première commande en attente
    return pending_commands[0]

async def schedule_enumeration_commands(scan_id: str):
    """Planifie les commandes d'énumération pour un scan"""
    # Commandes d'énumération de base
    commands = [
        {
            "id": str(uuid.uuid4()),
            "command": "netstat -tuln",
            "phase": "enumeration",
            "description": "Lister les ports ouverts"
        },
        {
            "id": str(uuid.uuid4()),
            "command": "ps aux",
            "phase": "enumeration",
            "description": "Lister les processus en cours d'exécution"
        },
        {
            "id": str(uuid.uuid4()),
            "command": "ls -la /etc/",
            "phase": "enumeration",
            "description": "Lister les fichiers de configuration"
        }
    ]
    
    # Ajouter les commandes à la liste
    for cmd in commands:
        active_scans[scan_id]["commands"].append(cmd)
    
    logger.info(f"Commandes d'énumération planifiées pour le scan {scan_id}")

async def schedule_vulnerability_scanning_commands(scan_id: str):
    """Planifie les commandes de recherche de vulnérabilités pour un scan"""
    # Commandes de recherche de vulnérabilités de base
    commands = [
        {
            "id": str(uuid.uuid4()),
            "command": "grep -i password /etc/passwd",
            "phase": "vulnerability_scanning",
            "description": "Rechercher des mots de passe en clair"
        },
        {
            "id": str(uuid.uuid4()),
            "command": "find / -type f -perm -04000 -ls 2>/dev/null",
            "phase": "vulnerability_scanning",
            "description": "Rechercher des fichiers SUID"
        },
        {
            "id": str(uuid.uuid4()),
            "command": "find / -type f -perm -02000 -ls 2>/dev/null",
            "phase": "vulnerability_scanning",
            "description": "Rechercher des fichiers SGID"
        }
    ]
    
    # Ajouter les commandes à la liste
    for cmd in commands:
        active_scans[scan_id]["commands"].append(cmd)
    
    logger.info(f"Commandes de recherche de vulnérabilités planifiées pour le scan {scan_id}")

async def schedule_exploitation_commands(scan_id: str):
    """Planifie les commandes d'exploitation pour un scan"""
    # Commandes d'exploitation de base (non destructives)
    commands = [
        {
            "id": str(uuid.uuid4()),
            "command": "cat /etc/shadow 2>/dev/null || echo 'Accès refusé'",
            "phase": "exploitation",
            "description": "Tenter d'accéder au fichier shadow"
        },
        {
            "id": str(uuid.uuid4()),
            "command": "ls -la /root 2>/dev/null || echo 'Accès refusé'",
            "phase": "exploitation",
            "description": "Tenter d'accéder au répertoire root"
        }
    ]
    
    # Ajouter les commandes à la liste
    for cmd in commands:
        active_scans[scan_id]["commands"].append(cmd)
    
    logger.info(f"Commandes d'exploitation planifiées pour le scan {scan_id}")

async def schedule_privilege_escalation_commands(scan_id: str):
    """Planifie les commandes d'élévation de privilèges pour un scan"""
    # Commandes d'élévation de privilèges de base (non destructives)
    commands = [
        {
            "id": str(uuid.uuid4()),
            "command": "sudo -l",
            "phase": "privilege_escalation",
            "description": "Lister les commandes sudo autorisées"
        },
        {
            "id": str(uuid.uuid4()),
            "command": "find / -writable -type d 2>/dev/null",
            "phase": "privilege_escalation",
            "description": "Rechercher des répertoires accessibles en écriture"
        }
    ]
    
    # Ajouter les commandes à la liste
    for cmd in commands:
        active_scans[scan_id]["commands"].append(cmd)
    
    logger.info(f"Commandes d'élévation de privilèges planifiées pour le scan {scan_id}")

async def schedule_cleanup_commands(scan_id: str):
    """Planifie les commandes de nettoyage pour un scan"""
    # Commandes de nettoyage de base
    commands = [
        {
            "id": str(uuid.uuid4()),
            "command": "echo 'Nettoyage terminé'",
            "phase": "cleanup",
            "description": "Finalisation du nettoyage"
        }
    ]
    
    # Ajouter les commandes à la liste
    for cmd in commands:
        active_scans[scan_id]["commands"].append(cmd)
    
    logger.info(f"Commandes de nettoyage planifiées pour le scan {scan_id}")

async def generate_report(scan_id: str):
    """Génère le rapport final pour un scan"""
    logger.info(f"Génération du rapport pour le scan {scan_id}")
    
    # Initialiser le statut du rapport
    scan_reports[scan_id] = {
        "status": "generating",
        "formats": []
    }
    
    # Simuler un délai pour la génération du rapport
    time.sleep(2)
    
    # Générer le rapport HTML
    html_report_path = REPORTS_DIR / f"{scan_id}_report.html"
    
    # Exemple de contenu HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rapport de Test de Pénétration</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            .section {{
                margin-bottom: 30px;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                padding: 12px 15px;
                border-bottom: 1px solid #ddd;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .vulnerability {{
                margin-bottom: 20px;
                padding: 15px;
                border-left: 4px solid;
            }}
            .critical {{
                border-color: #e74c3c;
                background-color: #fadbd8;
            }}
            .high {{
                border-color: #e67e22;
                background-color: #fae5d3;
            }}
            .medium {{
                border-color: #f1c40f;
                background-color: #fcf3cf;
            }}
            .low {{
                border-color: #3498db;
                background-color: #d6eaf8;
            }}
            .info {{
                border-color: #2ecc71;
                background-color: #d4efdf;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Rapport de Test de Pénétration Éthique</h1>
                <p>Date: {datetime.now().strftime('%d/%m/%Y')}</p>
            </header>
            
            <div class="section">
                <h2>Synthèse Technique</h2>
                <p>Ce rapport présente les résultats d'un test de pénétration éthique automatisé effectué sur le système cible. Plusieurs vulnérabilités ont été identifiées et sont détaillées ci-dessous.</p>
                
                <h3>Liste des Vulnérabilités</h3>
                
                <div class="vulnerability high">
                    <h4>Ports ouverts non sécurisés</h4>
                    <p><strong>Impact:</strong> Exposition potentielle de services sensibles à des attaques externes.</p>
                    <p><strong>Contexte métier:</strong> Ces ports ouverts pourraient permettre à un attaquant d'accéder à des services internes et de compromettre la confidentialité des données.</p>
                </div>
                
                <div class="vulnerability medium">
                    <h4>Fichiers avec permissions incorrectes</h4>
                    <p><strong>Impact:</strong> Accès non autorisé à des fichiers sensibles.</p>
                    <p><strong>Contexte métier:</strong> Des fichiers de configuration avec des permissions trop permissives pourraient exposer des informations sensibles.</p>
                </div>
            </div>
            
            <div class="section">
                <h2>Préconisations de Remédiations</h2>
                
                <h3>Sécurisation des ports ouverts</h3>
                <ul>
                    <li>Fermer tous les ports non nécessaires</li>
                    <li>Mettre en place un pare-feu pour filtrer les accès</li>
                    <li>Configurer des règles d'accès strictes pour les services exposés</li>
                </ul>
                
                <h3>Correction des permissions de fichiers</h3>
                <ul>
                    <li>Auditer et corriger les permissions des fichiers sensibles</li>
                    <li>Mettre en place une politique de gestion des droits d'accès</li>
                    <li>Effectuer des vérifications régulières des permissions</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Synthèse Managériale</h2>
                <p>Le test de pénétration a révélé plusieurs vulnérabilités qui, si exploitées, pourraient compromettre la sécurité des données et des systèmes de l'entreprise. Ces vulnérabilités sont particulièrement préoccupantes dans le contexte des exigences réglementaires actuelles et des risques pour la réputation de l'entreprise.</p>
                
                <p>Les principales préoccupations concernent:</p>
                <ul>
                    <li>La protection des données sensibles</li>
                    <li>La conformité aux réglementations en vigueur</li>
                    <li>La continuité des services critiques</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Plan d'Action</h2>
                <table>
                    <tr>
                        <th>Action</th>
                        <th>Priorité</th>
                        <th>Délai</th>
                        <th>ROI Sécurité</th>
                    </tr>
                    <tr>
                        <td>Sécurisation des ports ouverts</td>
                        <td>Haute</td>
                        <td>1 semaine</td>
                        <td>Élevé</td>
                    </tr>
                    <tr>
                        <td>Correction des permissions de fichiers</td>
                        <td>Moyenne</td>
                        <td>2 semaines</td>
                        <td>Moyen</td>
                    </tr>
                    <tr>
                        <td>Mise en place d'une surveillance continue</td>
                        <td>Moyenne</td>
                        <td>1 mois</td>
                        <td>Élevé</td>
                    </tr>
                    <tr>
                        <td>Formation des équipes à la sécurité</td>
                        <td>Basse</td>
                        <td>3 mois</td>
                        <td>Élevé</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Détails Techniques</h2>
                
                <h3>Informations Système</h3>
                <pre>{json.dumps(active_scans[scan_id]["system_info"], indent=2)}</pre>
                
                <h3>Résultats des Tests</h3>
                <pre>{json.dumps(active_scans[scan_id]["results"], indent=2)}</pre>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(html_report_path, "w") as f:
        f.write(html_content)
    
    # Générer le rapport PDF à partir du HTML
    from weasyprint import HTML
    
    pdf_report_path = REPORTS_DIR / f"{scan_id}_report.pdf"
    HTML(string=html_content).write_pdf(pdf_report_path)
    
    # Mettre à jour le statut du rapport
    scan_reports[scan_id] = {
        "status": "completed",
        "formats": ["html", "pdf"],
        "paths": {
            "html": str(html_report_path),
            "pdf": str(pdf_report_path)
        }
    }
    
    logger.info(f"Rapport généré pour le scan {scan_id}")

@app.post("/scan/result/{command_id}")
async def submit_command_result(
    command_id: str,
    result: CommandResult,
    scan_id: str = Depends(get_current_scan_id)
):
    """Soumet le résultat d'une commande exécutée"""
    # Vérifier si la commande existe
    command_exists = False
    for cmd in active_scans[scan_id]["commands"]:
        if cmd["id"] == command_id:
            command_exists = True
            break
    
    if not command_exists:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    # Enregistrer le résultat
    active_scans[scan_id]["results"][command_id] = {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Mettre à jour le progrès
    total_commands = len(active_scans[scan_id]["commands"])
    completed_commands = len(active_scans[scan_id]["results"])
    
    if total_commands > 0:
        phase_progress = completed_commands / total_commands
        # Ajuster le progrès global en fonction de la phase
        if active_scans[scan_id]["current_phase"] == "reconnaissance":
            active_scans[scan_id]["progress"] = 0.0 + (phase_progress * 0.2)
        elif active_scans[scan_id]["current_phase"] == "enumeration":
            active_scans[scan_id]["progress"] = 0.2 + (phase_progress * 0.2)
        elif active_scans[scan_id]["current_phase"] == "vulnerability_scanning":
            active_scans[scan_id]["progress"] = 0.4 + (phase_progress * 0.2)
        elif active_scans[scan_id]["current_phase"] == "exploitation":
            active_scans[scan_id]["progress"] = 0.6 + (phase_progress * 0.2)
        elif active_scans[scan_id]["current_phase"] == "privilege_escalation":
            active_scans[scan_id]["progress"] = 0.8 + (phase_progress * 0.1)
        elif active_scans[scan_id]["current_phase"] == "cleanup":
            active_scans[scan_id]["progress"] = 0.9 + (phase_progress * 0.05)
    
    logger.info(f"Résultat reçu pour la commande {command_id} du scan {scan_id}")
    
    return {"status": "success"}

@app.get("/scan/status")
async def get_scan_status(scan_id: str = Depends(get_current_scan_id)):
    """Récupère le statut d'un scan"""
    scan_data = active_scans[scan_id]
    
    # Calculer le temps estimé de fin
    start_time = datetime.fromisoformat(scan_data["start_time"])
    elapsed = datetime.utcnow() - start_time
    
    # Estimer le temps total en fonction du progrès
    if scan_data["progress"] > 0:
        estimated_total = elapsed / scan_data["progress"]
        estimated_remaining = estimated_total - elapsed
        estimated_end_time = (datetime.utcnow() + estimated_remaining).isoformat()
    else:
        estimated_end_time = None
    
    return {
        "scan_id": scan_id,
        "status": scan_data["status"],
        "progress": scan_data["progress"],
        "current_phase": scan_data["current_phase"],
        "start_time": scan_data["start_time"],
        "estimated_end_time": estimated_end_time
    }

@app.get("/report/final")
async def get_final_report(
    format: str = "pdf",
    scan_id: str = Depends(get_current_scan_id)
):
    """Récupère le rapport final d'un scan"""
    # Vérifier si le rapport est prêt
    if scan_id not in scan_reports or scan_reports[scan_id]["status"] != "completed":
        raise HTTPException(status_code=404, detail="Rapport non disponible")
    
    # Vérifier si le format demandé est disponible
    if format not in scan_reports[scan_id]["formats"]:
        raise HTTPException(status_code=400, detail=f"Format {format} non disponible")
    
    # Récupérer le chemin du rapport
    report_path = scan_reports[scan_id]["paths"][format]
    
    # Déterminer le type de contenu
    content_type = "application/pdf" if format == "pdf" else "text/html"
    
    # Retourner le fichier
    return FileResponse(
        path=report_path,
        media_type=content_type,
        filename=f"rapport_pentest_{scan_id}.{format}"
    )

# Point d'entrée pour l'exécution directe
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
