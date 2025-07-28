#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scanner Pro pour Windows - CyberShield Algeria
Version: 1.2.0
Description: Scanner de sécurité professionnel avec connexion au backend Docker
"""

import os
import sys
import json
import time
import socket
import platform
import subprocess
import requests
from datetime import datetime

# Configuration du scanner
CONFIG = {
    "version": "1.2.0",
    "name": "CyberShield Pro Scanner - Windows",
    "api_host": "localhost",
    "api_port": 8888,  # Port mis à jour pour correspondre à la configuration Docker
    "api_protocol": "http",
    "api_endpoint": "/api/scan/remote",
    "scan_timeout": 300,
    "report_dir": os.path.join(os.path.expanduser("~"), "CyberShield", "Reports")
}

def print_banner():
    """Affiche la bannière du scanner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ██████╗██╗   ██╗██████╗ ███████╗██████╗ ███████╗██╗  ██╗║
    ║  ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔════╝██║  ██║║
    ║  ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝███████╗███████║║
    ║  ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗╚════██║██╔══██║║
    ║  ╚██████╗   ██║   ██████╔╝███████╗██║  ██║███████║██║  ██║║
    ║   ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝║
    ║                                                           ║
    ║                    ALGERIA PRO SCANNER                    ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Version: {version}
    Mode: Professionnel avec connexion au backend Docker
    Date: {date}
    
    """.format(version=CONFIG["version"], date=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    print(banner)

def check_system():
    """Vérifie la compatibilité du système"""
    if platform.system() != "Windows":
        print("[ERREUR] Ce scanner est conçu pour Windows uniquement.")
        sys.exit(1)
    
    print("[INFO] Système compatible détecté: Windows " + platform.release())
    return True

def create_report_directory():
    """Crée le répertoire pour les rapports s'il n'existe pas"""
    if not os.path.exists(CONFIG["report_dir"]):
        try:
            os.makedirs(CONFIG["report_dir"])
            print(f"[INFO] Répertoire de rapports créé: {CONFIG['report_dir']}")
        except Exception as e:
            print(f"[ERREUR] Impossible de créer le répertoire de rapports: {str(e)}")
            sys.exit(1)
    return CONFIG["report_dir"]

def test_api_connection():
    """Teste la connexion à l'API backend"""
    api_url = f"{CONFIG['api_protocol']}://{CONFIG['api_host']}:{CONFIG['api_port']}/api/health"
    
    print(f"[INFO] Test de connexion à l'API: {api_url}")
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            print("[SUCCÈS] Connexion à l'API établie avec succès")
            return True
        else:
            print(f"[ERREUR] L'API a répondu avec le code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Impossible de se connecter à l'API: {str(e)}")
        print("[CONSEIL] Vérifiez que le conteneur Docker est en cours d'exécution et accessible")
        return False

def collect_system_info():
    """Collecte les informations système pour le scan"""
    system_info = {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "scan_time": datetime.now().isoformat()
    }
    
    print("[INFO] Collecte des informations système terminée")
    return system_info

def perform_local_scan():
    """Effectue un scan local préliminaire"""
    print("[INFO] Exécution du scan local préliminaire...")
    
    # Simuler un scan local
    scan_results = {
        "open_ports": [],
        "services": [],
        "vulnerabilities": []
    }
    
    # Scan des ports courants
    common_ports = [21, 22, 25, 80, 443, 3306, 3389, 8080]
    for port in common_ports:
        print(f"[SCAN] Vérification du port {port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(('127.0.0.1', port))
        if result == 0:
            scan_results["open_ports"].append(port)
            print(f"[TROUVÉ] Port {port} ouvert")
        sock.close()
    
    print("[INFO] Scan local préliminaire terminé")
    return scan_results

def send_to_remote_api(system_info, local_scan):
    """Envoie les données au backend pour analyse approfondie"""
    api_url = f"{CONFIG['api_protocol']}://{CONFIG['api_host']}:{CONFIG['api_port']}{CONFIG['api_endpoint']}"
    
    payload = {
        "system_info": system_info,
        "local_scan": local_scan,
        "scan_type": "full",
        "client_version": CONFIG["version"]
    }
    
    print(f"[INFO] Envoi des données au backend pour analyse: {api_url}")
    
    try:
        response = requests.post(api_url, json=payload, timeout=CONFIG["scan_timeout"])
        if response.status_code == 200:
            print("[SUCCÈS] Analyse distante terminée avec succès")
            return response.json()
        else:
            print(f"[ERREUR] L'API a répondu avec le code: {response.status_code}")
            print(f"[DÉTAIL] {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Échec de l'analyse distante: {str(e)}")
        return None

def generate_report(system_info, local_scan, remote_results):
    """Génère un rapport de sécurité complet"""
    report_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(CONFIG["report_dir"], f"cybershield_report_{report_time}.html")
    
    print(f"[INFO] Génération du rapport de sécurité: {report_file}")
    
    # Contenu du rapport HTML
    report_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rapport de Sécurité CyberShield</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #0a192f;
            }}
            .header {{
                background-color: #0a192f;
                color: #64ffda;
                padding: 20px;
                text-align: center;
                margin-bottom: 30px;
                border-radius: 5px;
            }}
            .section {{
                margin-bottom: 30px;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .vulnerability {{
                margin-bottom: 15px;
                padding: 15px;
                border-left: 4px solid;
            }}
            .critical {{
                border-color: #ff4d4d;
                background-color: #fff0f0;
            }}
            .high {{
                border-color: #ffa64d;
                background-color: #fff8f0;
            }}
            .medium {{
                border-color: #ffff4d;
                background-color: #fffff0;
            }}
            .low {{
                border-color: #4da6ff;
                background-color: #f0f8ff;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #0a192f;
                color: #64ffda;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding: 20px;
                font-size: 0.8em;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Rapport de Sécurité CyberShield</h1>
            <p>Généré le {datetime.now().strftime("%d/%m/%Y à %H:%M:%S")}</p>
        </div>
        
        <div class="section">
            <h2>Informations Système</h2>
            <table>
                <tr>
                    <th>Paramètre</th>
                    <th>Valeur</th>
                </tr>
                <tr>
                    <td>Nom d'hôte</td>
                    <td>{system_info["hostname"]}</td>
                </tr>
                <tr>
                    <td>Système d'exploitation</td>
                    <td>{system_info["os"]} {system_info["os_version"]}</td>
                </tr>
                <tr>
                    <td>Architecture</td>
                    <td>{system_info["architecture"]}</td>
                </tr>
                <tr>
                    <td>Processeur</td>
                    <td>{system_info["processor"]}</td>
                </tr>
                <tr>
                    <td>Date du scan</td>
                    <td>{datetime.fromisoformat(system_info["scan_time"]).strftime("%d/%m/%Y %H:%M:%S")}</td>
                </tr>
            </table>
        </div>
        
        <div class="section">
            <h2>Résultats du Scan Local</h2>
            <h3>Ports Ouverts</h3>
    """
    
    # Ajouter les ports ouverts
    if local_scan["open_ports"]:
        report_content += "<ul>"
        for port in local_scan["open_ports"]:
            report_content += f"<li>Port {port}</li>"
        report_content += "</ul>"
    else:
        report_content += "<p>Aucun port ouvert détecté.</p>"
    
    # Ajouter les résultats de l'analyse distante
    if remote_results:
        report_content += """
        </div>
        
        <div class="section">
            <h2>Résultats de l'Analyse Approfondie</h2>
        """
        
        # Vulnérabilités
        if "vulnerabilities" in remote_results and remote_results["vulnerabilities"]:
            report_content += "<h3>Vulnérabilités Détectées</h3>"
            
            for vuln in remote_results["vulnerabilities"]:
                severity_class = vuln.get("severity", "low").lower()
                report_content += f"""
                <div class="vulnerability {severity_class}">
                    <h4>{vuln.get("name", "Vulnérabilité inconnue")}</h4>
                    <p><strong>Sévérité:</strong> {vuln.get("severity", "Inconnue")}</p>
                    <p><strong>Description:</strong> {vuln.get("description", "Aucune description disponible.")}</p>
                    <p><strong>Impact:</strong> {vuln.get("impact", "Impact inconnu.")}</p>
                    <p><strong>Recommandation:</strong> {vuln.get("recommendation", "Aucune recommandation disponible.")}</p>
                </div>
                """
        else:
            report_content += "<p>Aucune vulnérabilité détectée.</p>"
        
        # Recommandations
        if "recommendations" in remote_results and remote_results["recommendations"]:
            report_content += "<h3>Recommandations de Sécurité</h3><ul>"
            for rec in remote_results["recommendations"]:
                report_content += f"<li>{rec}</li>"
            report_content += "</ul>"
    else:
        report_content += """
        </div>
        
        <div class="section">
            <h2>Résultats de l'Analyse Approfondie</h2>
            <p>L'analyse approfondie n'a pas pu être effectuée. Veuillez vérifier la connexion au backend.</p>
        """
    
    # Pied de page
    report_content += """
        </div>
        
        <div class="footer">
            <p>Ce rapport a été généré par CyberShield Algeria Pro Scanner.</p>
            <p>© 2025 CyberShield Algeria. Tous droits réservés.</p>
        </div>
    </body>
    </html>
    """
    
    # Écriture du rapport
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"[SUCCÈS] Rapport généré avec succès: {report_file}")
        return report_file
    except Exception as e:
        print(f"[ERREUR] Impossible de générer le rapport: {str(e)}")
        return None

def main():
    """Fonction principale du scanner"""
    print_banner()
    
    # Vérification du système
    check_system()
    
    # Création du répertoire de rapports
    create_report_directory()
    
    # Test de connexion à l'API
    if not test_api_connection():
        print("[ERREUR] Impossible de se connecter au backend. Le scan sera limité.")
        print("[CONSEIL] Vérifiez que le conteneur Docker est en cours d'exécution sur le port 8888")
        proceed = input("Voulez-vous continuer avec un scan local uniquement? (o/n): ")
        if proceed.lower() != "o":
            sys.exit(1)
    
    # Collecte des informations système
    print("\n[ÉTAPE 1/4] Collecte des informations système...")
    system_info = collect_system_info()
    
    # Scan local préliminaire
    print("\n[ÉTAPE 2/4] Exécution du scan local préliminaire...")
    local_scan = perform_local_scan()
    
    # Envoi au backend pour analyse approfondie
    print("\n[ÉTAPE 3/4] Envoi des données au backend pour analyse approfondie...")
    remote_results = send_to_remote_api(system_info, local_scan)
    
    # Génération du rapport
    print("\n[ÉTAPE 4/4] Génération du rapport de sécurité...")
    report_file = generate_report(system_info, local_scan, remote_results)
    
    if report_file:
        print(f"\n[TERMINÉ] Scan de sécurité terminé avec succès!")
        print(f"[RAPPORT] Le rapport est disponible ici: {report_file}")
        
        # Ouvrir le rapport automatiquement
        try:
            os.startfile(report_file)
        except:
            print(f"[INFO] Vous pouvez ouvrir le rapport manuellement à l'emplacement indiqué.")
    else:
        print("\n[ERREUR] Le scan s'est terminé avec des erreurs.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Scan interrompu par l'utilisateur.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERREUR CRITIQUE] Une erreur inattendue s'est produite: {str(e)}")
        sys.exit(1)
    
    # Attendre avant de fermer
    input("\nAppuyez sur Entrée pour quitter...")
