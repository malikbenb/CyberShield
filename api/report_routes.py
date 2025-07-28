from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import requests
from pydantic import BaseModel

from auth import get_current_user
from models import User, Scan, Vulnerability

# Modèles de données pour les rapports
class VulnerabilityWithSolution(BaseModel):
    id: int
    name: str
    description: str
    severity: str
    cvss_score: float
    solution: str
    solution_links: List[Dict[str, str]]
    references: List[str]

class EnhancedReport(BaseModel):
    scan_id: int
    scan_date: datetime
    target: str
    vulnerabilities: List[VulnerabilityWithSolution]
    summary: Dict[str, Any]

# Router pour les rapports enrichis
report_router = APIRouter(prefix="/api/reports", tags=["reports"])

# Base de données de solutions de vulnérabilités
# Dans une implémentation réelle, cela serait stocké dans une base de données
VULNERABILITY_SOLUTIONS = {
    "CVE-2021-44228": {  # Log4j
        "solution": "Mettre à jour Log4j vers la version 2.15.0 ou supérieure, ou désactiver la fonctionnalité JNDI.",
        "solution_links": [
            {"title": "Guide de mitigation Apache", "url": "https://logging.apache.org/log4j/2.x/security.html"},
            {"title": "CERT-FR - Alerte Log4Shell", "url": "https://www.cert.ssi.gouv.fr/alerte/CERTFR-2021-ALE-022/"},
            {"title": "ANSSI - Recommandations", "url": "https://www.ssi.gouv.fr/actualite/vulnerabilite-dans-log4j/"}
        ]
    },
    "CVE-2022-22965": {  # Spring4Shell
        "solution": "Mettre à jour Spring Framework vers la version 5.3.18 ou 5.2.20, ou appliquer les workarounds recommandés.",
        "solution_links": [
            {"title": "Guide de mitigation Spring", "url": "https://spring.io/blog/2022/03/31/spring-framework-rce-early-announcement"},
            {"title": "CERT-FR - Bulletin Spring4Shell", "url": "https://www.cert.ssi.gouv.fr/alerte/CERTFR-2022-ALE-001/"},
            {"title": "Tutoriel de correction", "url": "https://www.lunasec.io/docs/blog/spring-rce-vulnerabilities/"}
        ]
    },
    "CVE-2021-26855": {  # ProxyLogon (Exchange)
        "solution": "Installer les mises à jour de sécurité Microsoft pour Exchange Server.",
        "solution_links": [
            {"title": "Bulletin de sécurité Microsoft", "url": "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2021-26855"},
            {"title": "Guide de mitigation ANSSI", "url": "https://www.ssi.gouv.fr/actualite/vulnerabilites-microsoft-exchange-server/"},
            {"title": "Outil de vérification", "url": "https://github.com/microsoft/CSS-Exchange/tree/main/Security"}
        ]
    },
    "CVE-2021-34527": {  # PrintNightmare
        "solution": "Installer les mises à jour de sécurité Windows, désactiver le service d'impression ou restreindre l'accès au serveur d'impression.",
        "solution_links": [
            {"title": "Bulletin de sécurité Microsoft", "url": "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2021-34527"},
            {"title": "CERT-FR - Alerte PrintNightmare", "url": "https://www.cert.ssi.gouv.fr/alerte/CERTFR-2021-ALE-015/"},
            {"title": "Guide de mitigation détaillé", "url": "https://blog.truesec.com/2021/06/30/fix-for-printnightmare-cve-2021-1675-exploit-to-keep-your-print-servers-running/"}
        ]
    },
    "CVE-2021-40444": {  # MSHTML
        "solution": "Installer les mises à jour de sécurité Microsoft, désactiver l'installation des contrôles ActiveX, et utiliser le mode Microsoft Office Protected View.",
        "solution_links": [
            {"title": "Bulletin de sécurité Microsoft", "url": "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2021-40444"},
            {"title": "CERT-FR - Recommandations", "url": "https://www.cert.ssi.gouv.fr/alerte/CERTFR-2021-ALE-018/"},
            {"title": "Guide de protection", "url": "https://www.bleepingcomputer.com/news/security/microsoft-shares-more-mitigations-for-ongoing-mshtml-attacks/"}
        ]
    }
}

# Fonction pour enrichir les vulnérabilités avec des solutions
def enrich_vulnerability(vulnerability: Dict[str, Any]) -> VulnerabilityWithSolution:
    """Enrichit une vulnérabilité avec des solutions et des liens."""
    # Identifier les CVE dans la description ou les références
    cve_ids = []
    if "references" in vulnerability:
        for ref in vulnerability["references"]:
            if "CVE-" in ref:
                cve_id = ref.split("CVE-")[1].strip()
                if cve_id:
                    cve_ids.append(f"CVE-{cve_id}")
    
    # Chercher dans la description
    if "description" in vulnerability and "CVE-" in vulnerability["description"]:
        parts = vulnerability["description"].split("CVE-")
        for part in parts[1:]:
            cve_id = part.split()[0].strip()
            if cve_id:
                cve_ids.append(f"CVE-{cve_id}")
    
    # Chercher des solutions pour les CVE identifiés
    solution = "Aucune solution spécifique disponible. Consultez les meilleures pratiques générales de sécurité."
    solution_links = []
    
    for cve_id in cve_ids:
        if cve_id in VULNERABILITY_SOLUTIONS:
            solution = VULNERABILITY_SOLUTIONS[cve_id]["solution"]
            solution_links = VULNERABILITY_SOLUTIONS[cve_id]["solution_links"]
            break
    
    # Si aucune solution spécifique n'est trouvée, ajouter des liens génériques
    if not solution_links:
        solution_links = [
            {"title": "ANSSI - Guide d'hygiène informatique", "url": "https://www.ssi.gouv.fr/guide/guide-dhygiene-informatique/"},
            {"title": "OWASP - Guide de correction des vulnérabilités", "url": "https://owasp.org/www-project-web-security-testing-guide/"},
            {"title": "CIS - Contrôles de sécurité critiques", "url": "https://www.cisecurity.org/controls/"}
        ]
    
    # Enrichir avec des informations de la base NVD si disponible
    try:
        for cve_id in cve_ids:
            nvd_response = requests.get(f"https://services.nvd.nist.gov/rest/json/cve/1.0/{cve_id}")
            if nvd_response.status_code == 200:
                nvd_data = nvd_response.json()
                if "result" in nvd_data and "CVE_Items" in nvd_data["result"] and nvd_data["result"]["CVE_Items"]:
                    cve_item = nvd_data["result"]["CVE_Items"][0]
                    
                    # Ajouter des références supplémentaires
                    if "references" not in vulnerability:
                        vulnerability["references"] = []
                    
                    if "cve" in cve_item and "references" in cve_item["cve"] and "reference_data" in cve_item["cve"]["references"]:
                        for ref in cve_item["cve"]["references"]["reference_data"]:
                            if "url" in ref and ref["url"] not in vulnerability["references"]:
                                vulnerability["references"].append(ref["url"])
    except:
        # En cas d'erreur, continuer sans enrichissement NVD
        pass
    
    # Créer l'objet VulnerabilityWithSolution
    return VulnerabilityWithSolution(
        id=vulnerability.get("id", 0),
        name=vulnerability.get("name", "Vulnérabilité inconnue"),
        description=vulnerability.get("description", ""),
        severity=vulnerability.get("severity", "Medium"),
        cvss_score=vulnerability.get("cvss_score", 5.0),
        solution=solution,
        solution_links=solution_links,
        references=vulnerability.get("references", [])
    )

@report_router.get("/{scan_id}", response_model=EnhancedReport)
async def get_enhanced_report(scan_id: int, current_user: User = Depends(get_current_user)):
    """
    Récupère un rapport de scan enrichi avec des solutions pour les vulnérabilités.
    """
    # Dans une implémentation réelle, récupérer le scan et les vulnérabilités depuis la base de données
    # Ici, nous simulons des données
    
    # Vérifier que l'utilisateur a accès à ce scan
    # (Dans une implémentation réelle, vérifier dans la base de données)
    
    # Simuler la récupération d'un rapport
    with open("sample_report.json", "r") as f:
        report_data = json.load(f)
    
    # Enrichir chaque vulnérabilité avec des solutions
    enriched_vulnerabilities = [enrich_vulnerability(vuln) for vuln in report_data["vulnerabilities"]]
    
    # Créer le rapport enrichi
    enhanced_report = EnhancedReport(
        scan_id=scan_id,
        scan_date=datetime.fromisoformat(report_data["scan_date"]),
        target=report_data["target"],
        vulnerabilities=enriched_vulnerabilities,
        summary=report_data["summary"]
    )
    
    return enhanced_report

@report_router.get("/{scan_id}/pdf")
async def get_enhanced_report_pdf(scan_id: int, current_user: User = Depends(get_current_user)):
    """
    Génère un rapport PDF enrichi avec des solutions pour les vulnérabilités.
    """
    # Récupérer le rapport enrichi
    enhanced_report = await get_enhanced_report(scan_id, current_user)
    
    # Générer un PDF avec WeasyPrint
    from weasyprint import HTML, CSS
    from fastapi.responses import FileResponse
    import tempfile
    import os
    
    # Créer un fichier HTML temporaire
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_html:
        # Générer le contenu HTML du rapport
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Rapport de sécurité CyberShield - {enhanced_report.target}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    color: #333;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    max-width: 200px;
                    margin-bottom: 20px;
                }}
                .summary {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .vulnerability {{
                    margin-bottom: 30px;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .high {{
                    border-left: 5px solid #e74c3c;
                }}
                .medium {{
                    border-left: 5px solid #f39c12;
                }}
                .low {{
                    border-left: 5px solid #3498db;
                }}
                .info {{
                    border-left: 5px solid #2ecc71;
                }}
                .solution {{
                    background-color: #e8f4f8;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 10px;
                }}
                .solution-links {{
                    margin-top: 10px;
                }}
                .solution-links a {{
                    display: block;
                    margin-bottom: 5px;
                    color: #3498db;
                    text-decoration: none;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 50px;
                    font-size: 12px;
                    color: #7f8c8d;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <img src="logo.png" alt="CyberShield Logo" class="logo">
                <h1>Rapport de sécurité CyberShield</h1>
                <p>Date du scan: {enhanced_report.scan_date.strftime('%d/%m/%Y %H:%M')}</p>
                <p>Cible: {enhanced_report.target}</p>
            </div>
            
            <div class="summary">
                <h2>Résumé</h2>
                <table>
                    <tr>
                        <th>Sévérité</th>
                        <th>Nombre</th>
                    </tr>
                    <tr>
                        <td>Critique</td>
                        <td>{enhanced_report.summary.get('critical', 0)}</td>
                    </tr>
                    <tr>
                        <td>Élevée</td>
                        <td>{enhanced_report.summary.get('high', 0)}</td>
                    </tr>
                    <tr>
                        <td>Moyenne</td>
                        <td>{enhanced_report.summary.get('medium', 0)}</td>
                    </tr>
                    <tr>
                        <td>Faible</td>
                        <td>{enhanced_report.summary.get('low', 0)}</td>
                    </tr>
                    <tr>
                        <td>Informative</td>
                        <td>{enhanced_report.summary.get('info', 0)}</td>
                    </tr>
                </table>
            </div>
            
            <h2>Vulnérabilités détectées</h2>
        """
        
        # Ajouter chaque vulnérabilité
        for vuln in enhanced_report.vulnerabilities:
            severity_class = vuln.severity.lower() if vuln.severity.lower() in ["high", "medium", "low", "info"] else "medium"
            
            html_content += f"""
            <div class="vulnerability {severity_class}">
                <h3>{vuln.name}</h3>
                <p><strong>Sévérité:</strong> {vuln.severity}</p>
                <p><strong>Score CVSS:</strong> {vuln.cvss_score}</p>
                <p><strong>Description:</strong> {vuln.description}</p>
                
                <div class="solution">
                    <h4>Solution recommandée:</h4>
                    <p>{vuln.solution}</p>
                    
                    <div class="solution-links">
                        <h4>Liens utiles:</h4>
            """
            
            # Ajouter les liens de solution
            for link in vuln.solution_links:
                html_content += f"""
                        <a href="{link['url']}" target="_blank">{link['title']}</a>
                """
            
            html_content += """
                    </div>
                </div>
            """
            
            # Ajouter les références
            if vuln.references:
                html_content += """
                <div>
                    <h4>Références:</h4>
                    <ul>
                """
                
                for ref in vuln.references:
                    html_content += f"""
                        <li><a href="{ref}" target="_blank">{ref}</a></li>
                    """
                
                html_content += """
                    </ul>
                </div>
                """
            
            html_content += """
            </div>
            """
        
        # Ajouter le pied de page
        html_content += """
            <div class="footer">
                <p>Ce rapport a été généré automatiquement par CyberShield.</p>
                <p>© 2025 CyberShield. Tous droits réservés.</p>
            </div>
        </body>
        </html>
        """
        
        # Écrire le contenu HTML dans le fichier temporaire
        tmp_html.write(html_content.encode('utf-8'))
    
    # Créer un fichier PDF temporaire
    pdf_path = f"/tmp/cybershield_report_{scan_id}.pdf"
    
    # Générer le PDF à partir du HTML
    HTML(tmp_html.name).write_pdf(pdf_path)
    
    # Supprimer le fichier HTML temporaire
    os.unlink(tmp_html.name)
    
    # Renvoyer le fichier PDF
    return FileResponse(
        path=pdf_path,
        filename=f"cybershield_report_{scan_id}.pdf",
        media_type="application/pdf"
    )

# Fonction pour générer un exemple de rapport
def generate_sample_report():
    """Génère un exemple de rapport pour les tests."""
    sample_report = {
        "scan_id": 1,
        "scan_date": datetime.now().isoformat(),
        "target": "192.168.1.100",
        "vulnerabilities": [
            {
                "id": 1,
                "name": "Log4j Remote Code Execution (Log4Shell)",
                "description": "La bibliothèque Log4j est vulnérable à l'exécution de code à distance via la fonctionnalité JNDI. Cette vulnérabilité (CVE-2021-44228) permet à un attaquant d'exécuter du code arbitraire sur le serveur.",
                "severity": "Critical",
                "cvss_score": 10.0,
                "references": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-44228",
                    "https://logging.apache.org/log4j/2.x/security.html"
                ]
            },
            {
                "id": 2,
                "name": "Spring Framework RCE (Spring4Shell)",
                "description": "Le framework Spring est vulnérable à l'exécution de code à distance via la fonctionnalité Class Loader. Cette vulnérabilité (CVE-2022-22965) permet à un attaquant d'exécuter du code arbitraire sur le serveur.",
                "severity": "High",
                "cvss_score": 9.8,
                "references": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2022-22965",
                    "https://spring.io/blog/2022/03/31/spring-framework-rce-early-announcement"
                ]
            },
            {
                "id": 3,
                "name": "Microsoft Exchange Server RCE (ProxyLogon)",
                "description": "Microsoft Exchange Server est vulnérable à l'exécution de code à distance via la fonctionnalité SSRF. Cette vulnérabilité (CVE-2021-26855) permet à un attaquant d'exécuter du code arbitraire sur le serveur.",
                "severity": "Critical",
                "cvss_score": 9.8,
                "references": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-26855",
                    "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2021-26855"
                ]
            },
            {
                "id": 4,
                "name": "Windows Print Spooler RCE (PrintNightmare)",
                "description": "Le service Windows Print Spooler est vulnérable à l'exécution de code à distance. Cette vulnérabilité (CVE-2021-34527) permet à un attaquant d'exécuter du code arbitraire avec des privilèges SYSTEM.",
                "severity": "High",
                "cvss_score": 8.8,
                "references": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-34527",
                    "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2021-34527"
                ]
            },
            {
                "id": 5,
                "name": "Microsoft MSHTML RCE",
                "description": "Le composant MSHTML (Trident) est vulnérable à l'exécution de code à distance. Cette vulnérabilité (CVE-2021-40444) permet à un attaquant d'exécuter du code arbitraire via un document Office malveillant.",
                "severity": "High",
                "cvss_score": 8.8,
                "references": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-40444",
                    "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2021-40444"
                ]
            }
        ],
        "summary": {
            "critical": 2,
            "high": 3,
            "medium": 0,
            "low": 0,
            "info": 0
        }
    }
    
    # Enregistrer l'exemple de rapport dans un fichier JSON
    with open("sample_report.json", "w") as f:
        json.dump(sample_report, f, indent=2)
    
    return sample_report
