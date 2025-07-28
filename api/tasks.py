# Fichier: api/tasks.py

from celery_app import celery_app
from models import db, ScanHistory, Report
from datetime import datetime
import subprocess
import os
import json
import xmltodict
import requests
import time
import logging
import re 
from gvm.connections import TLSConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeTransform
from gvm.errors import GvmError
from xml.etree import ElementTree # Pour parser le XML GVM
from urllib.parse import quote, urlparse # Pour encoder les CPE/keywords et parser les URLs

# Configuration du logger
logger = logging.getLogger(__name__)

# --- Configuration API NVD ---
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_API_KEY = os.getenv("NVD_API_KEY") 
NVD_REQUEST_DELAY = 6 if not NVD_API_KEY else 0.6
NVD_RESULTS_PER_PAGE = 50 

# --- Configuration GVM --- 
GVM_HOST = os.getenv("GVM_HOST", "gvmd")
GVM_PORT = int(os.getenv("GVM_PORT", "9390"))
GVM_USER = os.getenv("GVM_USER", "admin")
GVM_PASSWORD = os.getenv("GVM_PASSWORD", "admin") 
SCAN_CONFIG_UUID = "daba56c8-73ec-11df-a475-002264764cea" 
SCANNER_UUID = "08b69003-5fc2-4037-a479-93b440673842" 
PORT_LIST_UUID = "730ef368-57e2-11e1-a90f-406186ea4fc5" 

# --- Fonctions Utilitaires NVD (inchangées) --- 

def _nvd_api_request(params):
    headers = {}
    delay = NVD_REQUEST_DELAY
    if NVD_API_KEY:
        headers["apiKey"] = NVD_API_KEY
        delay = NVD_REQUEST_DELAY_WITH_KEY # Correction: variable correcte
    else:
        logger.warning("Aucune clé API NVD fournie. Utilisation des limites de taux publiques.")
        
    time.sleep(delay) 
    try:
        response = requests.get(NVD_API_URL, headers=headers, params=params, timeout=45)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else "N/A"
        logger.error(f"Erreur lors de la requête NVD ({status_code}): {e} pour params {params}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la requête NVD: {e} pour params {params}", exc_info=True)
        return None

def get_cvss_score(cve_id):
    if not re.match(r"^CVE-\d{4}-\d{4,}$", cve_id, re.IGNORECASE):
        logger.warning(f"Format CVE invalide ignoré: {cve_id}")
        return None, None, None, None
    data = _nvd_api_request({"cveId": cve_id})
    if not data or data.get("totalResults", 0) == 0:
        logger.info(f"Aucun résultat trouvé dans NVD pour {cve_id}")
        return None, None, None, None
    try:
        vuln = data["vulnerabilities"][0]["cve"]
        description = "N/A"
        for desc_data in vuln.get("descriptions", []):
            if desc_data.get("lang") == "en":
                description = desc_data.get("value", "N/A")
                break
        cvss_v3_score = None
        cvss_v2_score = None
        severity = "UNKNOWN"
        if "cvssMetricV31" in vuln.get("metrics", {}):
            metrics_v31 = vuln["metrics"]["cvssMetricV31"][0]
            cvss_v3_score = metrics_v31["cvssData"]["baseScore"]
            severity = metrics_v31["cvssData"]["baseSeverity"]
        elif "cvssMetricV30" in vuln.get("metrics", {}):
            metrics_v30 = vuln["metrics"]["cvssMetricV30"][0]
            cvss_v3_score = metrics_v30["cvssData"]["baseScore"]
            severity = metrics_v30["cvssData"]["baseSeverity"]
        elif "cvssMetricV2" in vuln.get("metrics", {}):
            metrics_v2 = vuln["metrics"]["cvssMetricV2"][0]
            cvss_v2_score = metrics_v2["cvssData"]["baseScore"]
            severity = metrics_v2["baseSeverity"]
        logger.info(f"Score CVSS trouvé pour {cve_id}: v3={cvss_v3_score}, v2={cvss_v2_score}, Sévérité={severity}")
        return cvss_v3_score, cvss_v2_score, severity, description
    except (KeyError, IndexError, Exception) as e:
        logger.error(f"Erreur lors du parsing de la réponse NVD pour {cve_id}: {e}", exc_info=True)
        return None, None, None, None

def get_cves_for_cpe(cpe_string):
    if not cpe_string or not cpe_string.startswith("cpe:2.3:"):
        logger.warning(f"Format CPE invalide ignoré: {cpe_string}")
        return []
    logger.info(f"Recherche NVD pour CPE: {cpe_string}")
    found_cves = []
    start_index = 0
    total_results = 1
    while start_index < total_results:
        params = {"cpeName": cpe_string, "resultsPerPage": NVD_RESULTS_PER_PAGE, "startIndex": start_index}
        data = _nvd_api_request(params)
        if not data:
            logger.warning(f"Échec de la requête NVD pour CPE {cpe_string}, startIndex {start_index}")
            break
        total_results = data.get("totalResults", 0)
        if total_results == 0:
            logger.info(f"Aucun CVE trouvé pour CPE {cpe_string}")
            break
        vulnerabilities = data.get("vulnerabilities", [])
        for item in vulnerabilities:
            cve_data = item.get("cve")
            if cve_data:
                cve_id = cve_data.get("id")
                if cve_id:
                    found_cves.append(cve_id)
        start_index += len(vulnerabilities)
        if len(vulnerabilities) == 0 and start_index < total_results:
             logger.warning(f"Pagination NVD interrompue pour CPE {cpe_string}, incohérence détectée.")
             break
    logger.info(f"{len(found_cves)} CVE(s) potentiels trouvés pour CPE {cpe_string}")
    return list(set(found_cves))

def get_cves_for_keyword(keyword):
    if not keyword or len(keyword) < 3:
        logger.warning(f"Mot-clé de recherche NVD trop court ignoré: {keyword}")
        return []
    logger.info(f"Recherche NVD pour mot-clé: {keyword}")
    found_cves = []
    start_index = 0
    total_results = 1
    while start_index < total_results:
        params = {"keywordSearch": keyword, "keywordExactMatch": "", "resultsPerPage": NVD_RESULTS_PER_PAGE, "startIndex": start_index}
        data = _nvd_api_request(params)
        if not data:
            logger.warning(f"Échec de la requête NVD pour keyword {keyword}, startIndex {start_index}")
            break
        total_results = data.get("totalResults", 0)
        if total_results == 0:
            logger.info(f"Aucun CVE trouvé pour keyword {keyword}")
            break
        vulnerabilities = data.get("vulnerabilities", [])
        for item in vulnerabilities:
            cve_data = item.get("cve")
            if cve_data:
                cve_id = cve_data.get("id")
                if cve_id:
                    found_cves.append(cve_id)
        start_index += len(vulnerabilities)
        if len(vulnerabilities) == 0 and start_index < total_results:
             logger.warning(f"Pagination NVD interrompue pour keyword {keyword}, incohérence détectée.")
             break
    logger.info(f"{len(found_cves)} CVE(s) potentiels trouvés pour keyword {keyword}")
    return list(set(found_cves))

# --- Fonctions de Parsing (parse_nmap_xml, parse_nikto_json, parse_sqlmap_log, parse_gvm_xml inchangées) ---

def parse_nmap_xml(xml_content):
    open_ports_services = []
    if not xml_content:
        return open_ports_services
    try:
        data = xmltodict.parse(xml_content)
        if "nmaprun" not in data or "host" not in data["nmaprun"]:
            logger.warning("Format XML Nmap inattendu ou hôte non trouvé.")
            return open_ports_services
        hosts = data["nmaprun"]["host"]
        if not isinstance(hosts, list):
            hosts = [hosts]
        for host in hosts:
            host_status = host.get("@status", {}).get("@state")
            if host_status != "up":
                address_info = host.get("address", {})
                host_addr = address_info.get("@addr", "N/A")
                logger.info(f"Hôte {host_addr} non up ({host_status}), ignoré.")
                continue
            if "ports" in host and "port" in host["ports"]:
                ports = host["ports"]["port"]
                if not isinstance(ports, list):
                    ports = [ports]
                for port_info in ports:
                    if port_info.get("state", {}).get("@state") == "open":
                        service_info = port_info.get("service")
                        cpes = []
                        if service_info and "cpe" in service_info:
                            raw_cpes = service_info["cpe"]
                            if isinstance(raw_cpes, list):
                                cpes = [c for c in raw_cpes if isinstance(c, str)]
                            elif isinstance(raw_cpes, str):
                                cpes = [raw_cpes]
                        port_data = {
                            "port": port_info["@portid"],
                            "protocol": port_info["@protocol"],
                            "state": "open",
                            "service": service_info.get("@name", "unknown") if service_info else "unknown",
                            "product": service_info.get("@product", "") if service_info else "",
                            "version": service_info.get("@version", "") if service_info else "",
                            "extrainfo": service_info.get("@extrainfo", "") if service_info else "",
                            "cpe": cpes,
                            "scripts": [],
                            "vulnerabilities": []
                        }
                        if "script" in port_info:
                            scripts = port_info["script"]
                            if not isinstance(scripts, list):
                                scripts = [scripts]
                            for script in scripts:
                                port_data["scripts"].append({
                                    "id": script.get("@id"),
                                    "output": script.get("@output")
                                })
                        open_ports_services.append(port_data)
    except Exception as e:
        logger.error(f"Erreur lors du parsing du XML Nmap: {e}", exc_info=True)
    return open_ports_services

def parse_nikto_json(json_content):
    nikto_findings = []
    target_urls = set()
    if not json_content:
        return nikto_findings, list(target_urls)
    try:
        data = json.loads(json_content)
        if "vulnerabilities" in data:
            for vuln in data["vulnerabilities"]:
                finding = {
                    "id": vuln.get("id"),
                    "osvdb": vuln.get("OSVDB", []), 
                    "method": vuln.get("method"),
                    "url": vuln.get("url"),
                    "msg": vuln.get("msg"),
                    "references": vuln.get("references", []), 
                    "vulnerabilities": [] 
                }
                nikto_findings.append(finding)
                if vuln.get("url"): 
                    # Extraire la base URL (scheme + netloc)
                    parsed_url = urlparse(vuln["url"])
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    target_urls.add(base_url)
    except json.JSONDecodeError as e:
        logger.error(f"Erreur lors du parsing du JSON Nikto (JSON invalide): {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue lors du parsing du JSON Nikto: {e}", exc_info=True)
    return nikto_findings, list(target_urls)

def parse_sqlmap_log(log_content):
    sqlmap_findings = []
    if not log_content:
        return sqlmap_findings
    try:
        if "identified the following injection point(s)" in log_content:
            lines = log_content.splitlines()
            for i, line in enumerate(lines):
                if "Parameter:" in line and "Type:" in line:
                     details = line.strip()
                     url_found = "Unknown URL"
                     for j in range(max(0, i-5), i):
                         if lines[j].startswith("URL:"):
                             url_found = lines[j][4:].strip()
                             break
                     sqlmap_findings.append({
                         "type": "SQL Injection",
                         "details": details,
                         "url": url_found,
                         "vulnerabilities": [{
                             "cve": "N/A (SQL Injection)",
                             "score": 8.8, 
                             "severity": "HIGH",
                             "description": "Potential SQL Injection vulnerability identified by SQLMap."
                         }]
                     })
    except Exception as e:
        logger.error(f"Erreur lors du parsing du log SQLMap: {e}", exc_info=True)
    return sqlmap_findings

def parse_gvm_xml(xml_content):
    gvm_findings = []
    if not xml_content:
        return gvm_findings
    try:
        root = ElementTree.fromstring(xml_content)
        for result in root.findall(".//results/result"):
            name = result.findtext("name")
            host = result.findtext("host")
            port = result.findtext("port")
            threat = result.findtext("threat")
            severity_score = result.findtext("severity")
            description = result.findtext("description")
            nvt_oid = result.findtext("nvt/oid")
            cve_refs = result.findtext("nvt/refs/ref[@type=\"cve\"]")
            cvss_base_vector = result.findtext("nvt/cvss_base_vector")
            cvss_base_score = result.findtext("nvt/cvss_base")
            cves = []
            if cve_refs:
                cves = [cve.strip() for cve in cve_refs.split(",") if cve.strip()] 
            score_to_use = None
            severity = "UNKNOWN"
            if cvss_base_score:
                try:
                    score_to_use = float(cvss_base_score)
                    if score_to_use >= 7.0: severity = "HIGH"
                    elif score_to_use >= 4.0: severity = "MEDIUM"
                    else: severity = "LOW"
                except ValueError: pass
            elif severity_score:
                 try:
                     gvm_score_float = float(severity_score)
                     score_to_use = gvm_score_float
                     if gvm_score_float >= 7.0: severity = "HIGH"
                     elif gvm_score_float >= 4.0: severity = "MEDIUM"
                     elif gvm_score_float > 0.0: severity = "LOW"
                     else: severity = "INFO"
                 except ValueError: pass
            finding = {
                "name": name, "host": host, "port": port, "threat_level": threat,
                "gvm_severity_score": severity_score, "description": description,
                "nvt_oid": nvt_oid, "cves": cves, "cvss_base_vector": cvss_base_vector,
                "cvss_base_score_v2_gvm": cvss_base_score, "vulnerabilities": []
            }
            if score_to_use is not None and score_to_use > 0.0:
                 finding["vulnerabilities"].append({
                     "cve": cves[0] if cves else f"NVT:{nvt_oid}",
                     "score": score_to_use, "severity": severity, "description": description
                 })
            gvm_findings.append(finding)
    except ElementTree.ParseError as e:
        logger.error(f"Erreur de parsing XML GVM: {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue lors du parsing XML GVM: {e}", exc_info=True)
    return gvm_findings

def parse_gobuster_output(output_content):
    """Parse la sortie standard de Gobuster pour extraire les chemins trouvés."""
    gobuster_findings = []
    if not output_content:
        return gobuster_findings
    try:
        # Regex pour capturer les lignes de résultats (chemin et statut)
        # Exemple: /admin (Status: 200)
        # Exemple: /images (Status: 301) -> http://target/images/
        # Exemple: Found: /config.php (Status: 200)
        pattern = re.compile(r"^(?:Found: )?(/[^\s(]+)\s+\(Status: (\d{3})\)")
        lines = output_content.splitlines()
        for line in lines:
            match = pattern.search(line)
            if match:
                path = match.group(1)
                status_code = int(match.group(2))
                gobuster_findings.append({
                    "path": path,
                    "status_code": status_code
                })
    except Exception as e:
        logger.error(f"Erreur lors du parsing de la sortie Gobuster: {e}", exc_info=True)
    return gobuster_findings

# --- Fonction d\Enrichissement CVSS (inchangée) ---

def enrich_findings_with_cvss(report_data):
    max_cvss_score = 0.0
    processed_cves = set()
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0, "unknown": 0}
    logger.info("Enrichissement des résultats Nmap...")
    for finding in report_data.get("nmap_findings", []):
        potential_cves_for_finding = set()
        if finding.get("cpe"): 
            for cpe_str in finding["cpe"]:
                cves_from_cpe = get_cves_for_cpe(cpe_str)
                potential_cves_for_finding.update(cves_from_cpe)
        keyword_parts = [finding.get("product"), finding.get("version"), finding.get("service")]
        keyword = " ".join(filter(None, keyword_parts)).strip()
        if keyword and not potential_cves_for_finding:
            cves_from_keyword = get_cves_for_keyword(keyword)
            potential_cves_for_finding.update(cves_from_keyword)
        for cve_id in potential_cves_for_finding:
            cve_id = cve_id.upper()
            if cve_id not in processed_cves:
                processed_cves.add(cve_id)
                cvss_v3, cvss_v2, severity, description = get_cvss_score(cve_id)
                score_to_use = cvss_v3 if cvss_v3 is not None else cvss_v2
                if score_to_use is not None:
                    finding["vulnerabilities"].append({
                        "cve": cve_id, "cvss_v3": cvss_v3, "cvss_v2": cvss_v2,
                        "score": score_to_use, "severity": severity, "description": description,
                        "source": "Nmap (CPE/Keyword)"
                    })
                    max_cvss_score = max(max_cvss_score, score_to_use)
                    if severity: summary[severity.lower()] += 1
                    else: summary["unknown"] += 1
                else:
                    finding["vulnerabilities"].append({"cve": cve_id, "score": None, "severity": "UNKNOWN", "source": "Nmap (CPE/Keyword)"})
                    summary["unknown"] += 1
            else:
                 already_found = False
                 for v in finding["vulnerabilities"]:
                     if v.get("cve") == cve_id:
                         already_found = True
                         break
                 if not already_found:
                     finding["vulnerabilities"].append({"cve": cve_id, "score": "(processed)", "severity": "(processed)", "source": "Nmap (CPE/Keyword)"})
        if finding.get("service") == "telnet":
             telnet_vuln_exists = any(v.get("cve") == "N/A (Telnet)" for v in finding["vulnerabilities"])
             if not telnet_vuln_exists:
                 finding["vulnerabilities"].append({
                     "cve": "N/A (Telnet)", "score": 7.5, "severity": "HIGH",
                     "description": "Telnet service detected, which is insecure.", "source": "Nmap (Service)"
                 })
                 max_cvss_score = max(max_cvss_score, 7.5)
                 summary["high"] += 1
    logger.info("Enrichissement des résultats Nikto...")
    for finding in report_data.get("nikto_findings", []):
        cves_found = set()
        refs_str = json.dumps(finding.get("references", [])) + finding.get("msg", "")
        potential_cves = re.findall(r"CVE-\d{4}-\d{4,}", refs_str, re.IGNORECASE)
        cves_found.update(potential_cves)
        for cve_id in cves_found:
            cve_id = cve_id.upper()
            if cve_id not in processed_cves:
                processed_cves.add(cve_id)
                cvss_v3, cvss_v2, severity, description = get_cvss_score(cve_id)
                score_to_use = cvss_v3 if cvss_v3 is not None else cvss_v2
                if score_to_use is not None:
                    finding["vulnerabilities"].append({
                        "cve": cve_id, "cvss_v3": cvss_v3, "cvss_v2": cvss_v2,
                        "score": score_to_use, "severity": severity, "description": description,
                        "source": "Nikto"
                    })
                    max_cvss_score = max(max_cvss_score, score_to_use)
                    if severity: summary[severity.lower()] += 1
                    else: summary["unknown"] += 1
                else:
                    finding["vulnerabilities"].append({"cve": cve_id, "score": None, "severity": "UNKNOWN", "source": "Nikto"})
                    summary["unknown"] += 1
    logger.info("Enrichissement des résultats SQLMap...")
    for finding in report_data.get("sqlmap_findings", []):
        for vuln in finding.get("vulnerabilities", []):
             score = vuln.get("score")
             severity = vuln.get("severity")
             if score is not None:
                 max_cvss_score = max(max_cvss_score, score)
             if severity: summary[severity.lower()] += 1
             else: summary["unknown"] += 1
    logger.info("Enrichissement des résultats GVM...")
    for finding in report_data.get("gvm_findings", []):
        for cve_id in finding.get("cves", []):
            cve_id = cve_id.upper()
            if cve_id not in processed_cves:
                processed_cves.add(cve_id)
                cvss_v3, cvss_v2, severity_nvd, description_nvd = get_cvss_score(cve_id)
                score_nvd = cvss_v3 if cvss_v3 is not None else cvss_v2
                if score_nvd is not None:
                    found_vuln = False
                    for vuln in finding["vulnerabilities"]:
                        if vuln.get("cve") == cve_id:
                            vuln.update({"cvss_v3": cvss_v3, "cvss_v2": cvss_v2, "score": score_nvd, "severity": severity_nvd, "description": description_nvd, "source": "GVM (CVE) + NVD"})
                            found_vuln = True
                            break
                    if not found_vuln:
                         finding["vulnerabilities"].append({
                             "cve": cve_id, "cvss_v3": cvss_v3, "cvss_v2": cvss_v2,
                             "score": score_nvd, "severity": severity_nvd, "description": description_nvd,
                             "source": "GVM (CVE) + NVD"
                         })
                    max_cvss_score = max(max_cvss_score, score_nvd)
                    if severity_nvd: summary[severity_nvd.lower()] += 1
                    else: summary["unknown"] += 1
                else:
                    for vuln in finding["vulnerabilities"]:
                         if vuln.get("cve") == cve_id and vuln.get("score") is not None:
                             max_cvss_score = max(max_cvss_score, vuln["score"])
                             if vuln.get("severity"): summary[vuln["severity"].lower()] += 1
                             else: summary["unknown"] += 1
                             vuln["source"] = "GVM (CVE)"
                             break 
                    else: 
                         summary["unknown"] += 1
            else:
                 for vuln in finding["vulnerabilities"]:
                     if vuln.get("cve") == cve_id and vuln.get("score") is not None:
                         max_cvss_score = max(max_cvss_score, vuln["score"])
                         break
        if not finding.get("cves"):
             for vuln in finding["vulnerabilities"]:
                 if vuln.get("score") is not None:
                     max_cvss_score = max(max_cvss_score, vuln["score"])
                     if vuln.get("severity"): summary[vuln["severity"].lower()] += 1
                     else: summary["unknown"] += 1
                     vuln["source"] = "GVM (NVT)"
                     break
    report_data["vulnerability_summary"] = summary
    logger.info(f"Enrichissement CVSS terminé. Score max final: {max_cvss_score}, Sommaire: {summary}")
    return report_data, max_cvss_score

# --- Fonctions Outils (run_nmap, run_nikto, run_sqlmap, run_gvm_scan inchangées) ---

def run_nmap(target_ip, result_dir, log_file):
    logger.info(f"Exécution de Nmap sur {target_ip} avec scripts vuln,vulners")
    output_file = os.path.join(result_dir, "nmap_results.xml")
    command = [
        "docker", "run", "--rm", "--network=host", 
        "-v", f"{result_dir}:/data", 
        "instrumentisto/nmap",
        "-sS", "-A", "-T4", "--script", "vuln,vulners", "-oX", "/data/nmap_results.xml", target_ip
    ]
    try:
        with open(log_file, "a") as lf:
            lf.write(f"\n--- Nmap Command ---\n{' '.join(command)}\n")
            process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=1800) 
            lf.write(f"--- Nmap Stdout ---\n{process.stdout}\n")
            lf.write(f"--- Nmap Stderr ---\n{process.stderr}\n")
        if process.returncode != 0:
            logger.warning(f"Nmap terminé avec code {process.returncode}")
        logger.info("Nmap terminé.")
        if os.path.exists(output_file):
             with open(output_file, "r") as f:
                 return True, f.read()
        else:
             logger.warning("Fichier de résultats Nmap non trouvé.")
             return True, ""
    except subprocess.TimeoutExpired:
        logger.error(f"Nmap a dépassé le timeout pour {target_ip}")
        return False, "Nmap command timed out."
    except Exception as e:
        logger.error(f"Erreur lors de l\exécution de Nmap: {e}", exc_info=True)
        return False, f"Error running Nmap: {e}"

def run_nikto(target_ip, result_dir, log_file):
    logger.info(f"Exécution de Nikto sur {target_ip}")
    output_file = os.path.join(result_dir, "nikto_results.json")
    base_urls = set()
    # Essayer de détecter les ports web ouverts depuis Nmap (si Nmap a déjà tourné)
    nmap_file = os.path.join(result_dir, "nmap_results.xml")
    web_ports = {"80", "443"} # Ports par défaut
    if os.path.exists(nmap_file):
        try:
            with open(nmap_file, "r") as f:
                nmap_data = parse_nmap_xml(f.read())
                for port_info in nmap_data:
                    if "http" in port_info.get("service", "") or port_info.get("port") in ["80", "443", "8080", "8443"]:
                        web_ports.add(port_info["port"])
        except Exception as e:
            logger.warning(f"Impossible de lire les ports Nmap pour Nikto: {e}")

    nikto_results_content = ""
    nikto_overall_success = True

    for port in web_ports:
        protocol = "https" if port in ["443", "8443"] else "http"
        target_url = f"{protocol}://{target_ip}:{port}" if port not in ["80", "443"] else f"{protocol}://{target_ip}"
        
        # Vérifier si le port est réellement accessible
        try:
            requests.get(target_url, timeout=10, verify=False)
            logger.info(f"Port {port} ({protocol}) semble ouvert. Lancement de Nikto sur {target_url}")
            base_urls.add(target_url)
        except requests.exceptions.RequestException:
            logger.info(f"Port {port} ({protocol}) non accessible pour Nikto sur {target_ip}. Ignoré.")
            continue
            
        command = [
            "docker", "run", "--rm",
            "-v", f"{result_dir}:/data",
            "sullo/nikto",
            "-h", target_url,
            "-Format", "json", "-o", f"/data/nikto_results_{port}.json",
            "-Tuning", "x 6"
        ]
        try:
            with open(log_file, "a") as lf:
                lf.write(f"\n--- Nikto Command ({target_url}) ---\n{' '.join(command)}\n")
                process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=900)
                lf.write(f"--- Nikto Stdout ({target_url}) ---\n{process.stdout}\n")
                lf.write(f"--- Nikto Stderr ({target_url}) ---\n{process.stderr}\n")
            if process.returncode != 0:
                logger.warning(f"Nikto terminé avec code {process.returncode} pour {target_url}")
            port_output_file = os.path.join(result_dir, f"nikto_results_{port}.json")
            if os.path.exists(port_output_file):
                 with open(port_output_file, "r") as f:
                     # Fusionner les résultats JSON (simpliste: concaténer les listes de vuln)
                     try:
                         current_data = json.loads(nikto_results_content) if nikto_results_content else {"vulnerabilities": []}
                         new_data = json.loads(f.read())
                         current_data["vulnerabilities"].extend(new_data.get("vulnerabilities", []))
                         nikto_results_content = json.dumps(current_data)
                     except json.JSONDecodeError:
                         logger.error(f"Erreur JSON lors de la fusion des résultats Nikto pour le port {port}")
                         nikto_overall_success = False
            else:
                 logger.warning(f"Fichier de résultats Nikto non trouvé pour le port {port}.")
        except subprocess.TimeoutExpired:
            logger.error(f"Nikto a dépassé le timeout pour {target_url}")
            nikto_overall_success = False
            nikto_results_content += f"\nERROR: Nikto timed out for {target_url}\n"
        except Exception as e:
            logger.error(f"Erreur lors de l\exécution de Nikto pour {target_url}: {e}", exc_info=True)
            nikto_overall_success = False
            nikto_results_content += f"\nERROR: Exception during Nikto for {target_url}: {e}\n"
            
    logger.info("Nikto terminé pour tous les ports web détectés.")
    # Sauvegarder le résultat JSON fusionné
    if nikto_results_content:
         with open(output_file, "w") as f:
             f.write(nikto_results_content)
             
    return nikto_overall_success, nikto_results_content, list(base_urls)

def run_sqlmap(target_urls, result_dir, log_file):
    if not target_urls:
        logger.info("Aucune URL cible fournie pour SQLMap.")
        return True, ""
    logger.info(f"Exécution de SQLMap sur {len(target_urls)} URL(s)")
    output_log = os.path.join(result_dir, "sqlmap_results.log")
    success = True
    log_content = ""
    for url in target_urls:
        logger.info(f"Scan SQLMap sur : {url}")
        session_dir_name = f"sqlmap_session_{re.sub(r'[^a-zA-Z0-9]+', '_', urlparse(url).netloc)}_{int(time.time()) % 10000}" # Nom de session unique
        session_dir_path = f"/data/{session_dir_name}"
        command = [
            "docker", "run", "--rm",
            "-v", f"{result_dir}:/data",
            "fallard/sqlmap",
            "-u", url,
            "--batch", # Non interactif
            "--output-dir", session_dir_path,
            "--level=3", "--risk=2", # Niveaux de test
            "--random-agent" # Utiliser un User-Agent aléatoire
        ]
        try:
            with open(log_file, "a") as lf:
                lf.write(f"\n--- SQLMap Command ({url}) ---\n{' '.join(command)}\n")
                process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=1800)
                lf.write(f"--- SQLMap Stdout ({url}) ---\n{process.stdout}\n")
                lf.write(f"--- SQLMap Stderr ({url}) ---\n{process.stderr}\n")
            if process.returncode != 0:
                logger.warning(f"SQLMap terminé avec code {process.returncode} pour {url}")
            # Lire le log généré par sqlmap s\il existe
            sqlmap_log_path = os.path.join(result_dir, session_dir_name, "log")
            if os.path.exists(sqlmap_log_path):
                 with open(sqlmap_log_path, "r") as slf:
                     log_content += f"\n--- SQLMap Log ({url}) ---\n" + slf.read() + "\n"
            else:
                 log_content += process.stdout + "\n" # Fallback sur stdout
        except subprocess.TimeoutExpired:
            logger.error(f"SQLMap a dépassé le timeout pour {url}")
            success = False
            log_content += f"\nERROR: SQLMap timed out for {url}\n"
        except Exception as e:
            logger.error(f"Erreur lors de l\exécution de SQLMap pour {url}: {e}", exc_info=True)
            success = False
            log_content += f"\nERROR: Exception during SQLMap for {url}: {e}\n"
    logger.info("SQLMap terminé.")
    # Sauvegarder le log consolidé
    with open(output_log, "w") as f:
        f.write(log_content)
    return success, log_content

def run_gvm_scan(target_ip, result_dir, log_file):
    logger.info(f"Démarrage du processus de scan GVM pour {target_ip}")
    gmp = None
    try:
        logger.info(f"Connexion à GVM sur {GVM_HOST}:{GVM_PORT}")
        connection = TLSConnection(hostname=GVM_HOST, port=GVM_PORT)
        transform = EtreeTransform()
        with Gmp(connection=connection, transform=transform) as gmp:
            gmp.authenticate(username=GVM_USER, password=GVM_PASSWORD)
            logger.info("Authentification GVM réussie.")
            target_name = f"Target_{target_ip}_{int(time.time())}"
            logger.info(f"Création de la cible GVM: {target_name}")
            response = gmp.create_target(name=target_name, hosts=[target_ip], port_list_id=PORT_LIST_UUID)
            target_id = response.xpath("//target/@id")[0]
            logger.info(f"Cible GVM créée avec ID: {target_id}")
            task_name = f"Scan_{target_ip}_{int(time.time())}"
            logger.info(f"Création de la tâche GVM: {task_name}")
            response = gmp.create_task(name=task_name, config_id=SCAN_CONFIG_UUID, target_id=target_id, scanner_id=SCANNER_UUID)
            task_id = response.xpath("//task/@id")[0]
            logger.info(f"Tâche GVM créée avec ID: {task_id}. Démarrage du scan...")
            gmp.start_task(task_id=task_id)
            max_wait_time = 7200 
            start_wait_time = time.time()
            while True:
                if time.time() - start_wait_time > max_wait_time:
                    logger.error(f"Timeout dépassé en attendant la fin du scan GVM {task_id}")
                    try: gmp.stop_task(task_id) 
                    except: pass
                    return False, "GVM scan timed out."
                task_status_resp = gmp.get_task(task_id=task_id)
                status = task_status_resp.xpath("//task/status/text()")[0]
                progress = task_status_resp.xpath("//task/progress/text()")[0]
                logger.info(f"Statut scan GVM {task_id}: {status}, Progression: {progress}%" )
                if status == "Done":
                    logger.info(f"Scan GVM {task_id} terminé.")
                    break
                elif status in ["Stopped", "Delete Requested", "Error"]:
                    logger.error(f"Scan GVM {task_id} terminé avec un statut inattendu: {status}")
                    return False, f"GVM scan finished with unexpected status: {status}"
                time.sleep(60)
            logger.info(f"Récupération du rapport pour le scan GVM {task_id}")
            report_resp = gmp.get_reports(task_id=task_id, filter_string="status=Done")
            report_id = report_resp.xpath("//report/@id")[0]
            report_format_id = "a994b278-1f62-11e1-96ac-406186ea4fc5"
            download_resp = gmp.get_report(report_id=report_id, report_format_id=report_format_id)
            report_element = download_resp.find("report")
            if report_element is None:
                 logger.error("Élément <report> non trouvé dans la réponse GVM.")
                 return False, "Failed to find report element in GVM response."
            report_content_base64 = report_element.text
            import base64
            report_content_xml = base64.b64decode(report_content_base64).decode("utf-8")
            output_file = os.path.join(result_dir, "gvm_results.xml")
            with open(output_file, "w") as f:
                f.write(report_content_xml)
            logger.info(f"Rapport GVM sauvegardé dans {output_file}")
            try:
                logger.info(f"Nettoyage de la tâche GVM {task_id} et de la cible {target_id}")
                gmp.delete_task(task_id=task_id, ultimate=True)
                gmp.delete_target(target_id=target_id, ultimate=True)
            except GvmError as e:
                logger.warning(f"Erreur lors du nettoyage GVM: {e}")
            return True, report_content_xml
    except GvmError as e:
        logger.error(f"Erreur GVM lors du scan de {target_ip}: {e}", exc_info=True)
        return False, f"GVM Error: {e}"
    except Exception as e:
        logger.error(f"Erreur inattendue lors du scan GVM de {target_ip}: {e}", exc_info=True)
        return False, f"Unexpected error during GVM scan: {e}"

def run_gobuster(target_urls, result_dir, log_file):
    """Exécute Gobuster sur les URLs web fournies."""
    if not target_urls:
        logger.info("Aucune URL cible fournie pour Gobuster.")
        return True, ""
    logger.info(f"Exécution de Gobuster sur {len(target_urls)} URL(s)")
    output_file = os.path.join(result_dir, "gobuster_results.txt")
    success = True
    gobuster_output = ""
    # Utiliser une wordlist commune (présente dans l\image Docker ojjar/gobuster)
    wordlist = "/usr/share/wordlists/dirb/common.txt" 

    for url in target_urls:
        logger.info(f"Scan Gobuster sur : {url}")
        command = [
            "docker", "run", "--rm",
            "ojjar/gobuster",
            "dir",
            "-u", url,
            "-w", wordlist,
            "-t", "50", # Nombre de threads
            "-q", # Mode silencieux (moins de bruit)
            "--no-error", # Ne pas afficher les erreurs de connexion
            "-k" # Ignorer les erreurs SSL
        ]
        try:
            with open(log_file, "a") as lf:
                lf.write(f"\n--- Gobuster Command ({url}) ---\n{' '.join(command)}\n")
                process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=600)
                lf.write(f"--- Gobuster Stdout ({url}) ---\n{process.stdout}\n")
                lf.write(f"--- Gobuster Stderr ({url}) ---\n{process.stderr}\n")
            if process.returncode != 0:
                logger.warning(f"Gobuster terminé avec code {process.returncode} pour {url}")
            gobuster_output += f"\n--- Results for {url} ---\n" + process.stdout + "\n"
        except subprocess.TimeoutExpired:
            logger.error(f"Gobuster a dépassé le timeout pour {url}")
            success = False
            gobuster_output += f"\nERROR: Gobuster timed out for {url}\n"
        except Exception as e:
            logger.error(f"Erreur lors de l\exécution de Gobuster pour {url}: {e}", exc_info=True)
            success = False
            gobuster_output += f"\nERROR: Exception during Gobuster for {url}: {e}\n"
            
    logger.info("Gobuster terminé.")
    # Sauvegarder la sortie consolidée
    with open(output_file, "w") as f:
        f.write(gobuster_output)
    return success, gobuster_output

# --- Tâche Celery Principale --- 

@celery_app.task(bind=True, max_retries=1, default_retry_delay=60)
def run_scan(self, scan_id, target_ip):
    logger.info(f"[Scan {scan_id}] Démarrage du scan pour {target_ip}")
    scan_history = None
    result_dir = f"/app/scan_results/{scan_id}" 
    log_file = os.path.join(result_dir, "scan.log")
    final_report_data = {
        "scan_id": scan_id,
        "target_ip": target_ip,
        "start_time": datetime.utcnow().isoformat(),
        "tools_used": [],
        "nmap_findings": [],
        "nikto_findings": [],
        "sqlmap_findings": [],
        "gvm_findings": [],
        "gobuster_findings": [], # Ajout pour Gobuster
        "vulnerability_summary": {},
        "errors": []
    }
    max_score = 0.0
    overall_status = "completed"
    web_target_urls = [] # URLs détectées par Nmap/Nikto

    try:
        os.makedirs(result_dir, exist_ok=True)
        with open(log_file, "w") as lf:
             lf.write(f"Scan Log for ID: {scan_id}, Target: {target_ip}\n")
             start_time_val = final_report_data.get('start_time', 'N/A')
             lf.write(f"Started at: {start_time_val}\n")


        scan_history = ScanHistory.query.get(scan_id)
        if not scan_history:
            logger.error(f"[Scan {scan_id}] ScanHistory non trouvé.")
            return
        scan_history.status = "running"
        db.session.commit()
        logger.info(f"[Scan {scan_id}] Statut mis à jour en \"running\"")

        # --- Exécution des outils --- 
        # Nmap
        final_report_data["tools_used"].append("Nmap")
        nmap_success, nmap_result = run_nmap(target_ip, result_dir, log_file)
        if nmap_success:
            final_report_data["nmap_findings"] = parse_nmap_xml(nmap_result)
        else:
            final_report_data["errors"].append(f"Nmap failed: {nmap_result}")
            overall_status = "completed_with_errors"

        # Nikto (détecte aussi les URLs web)
        final_report_data["tools_used"].append("Nikto")
        nikto_success, nikto_result, nikto_target_urls = run_nikto(target_ip, result_dir, log_file)
        if nikto_success:
            final_report_data["nikto_findings"], _ = parse_nikto_json(nikto_result) # On a déjà les URLs
            web_target_urls.extend(nikto_target_urls)
        else:
            final_report_data["errors"].append(f"Nikto failed: {nikto_result}")
            overall_status = "completed_with_errors"
            
        web_target_urls = list(set(web_target_urls)) # Dédoublonner

        # Gobuster (sur les URLs web trouvées)
        if web_target_urls:
            final_report_data["tools_used"].append("Gobuster")
            gobuster_success, gobuster_result = run_gobuster(web_target_urls, result_dir, log_file)
            if gobuster_success:
                final_report_data["gobuster_findings"] = parse_gobuster_output(gobuster_result)
            else:
                final_report_data["errors"].append(f"Gobuster failed or timed out.")
                overall_status = "completed_with_errors"
        else:
            logger.info(f"[Scan {scan_id}] Aucune URL web trouvée, Gobuster non exécuté.")

        # SQLMap (sur les URLs web trouvées)
        if web_target_urls:
            final_report_data["tools_used"].append("SQLMap")
            sqlmap_success, sqlmap_result = run_sqlmap(web_target_urls, result_dir, log_file)
            if sqlmap_success:
                final_report_data["sqlmap_findings"] = parse_sqlmap_log(sqlmap_result)
            else:
                final_report_data["errors"].append(f"SQLMap failed or timed out.")
                overall_status = "completed_with_errors"
        else:
             logger.info(f"[Scan {scan_id}] Aucune URL web trouvée, SQLMap non exécuté.")

        # GVM
        final_report_data["tools_used"].append("GVM/OpenVAS")
        gvm_success, gvm_result = run_gvm_scan(target_ip, result_dir, log_file)
        if gvm_success:
            final_report_data["gvm_findings"] = parse_gvm_xml(gvm_result)
        else:
            final_report_data["errors"].append(f"GVM scan failed: {gvm_result}")
            overall_status = "completed_with_errors"

        # --- Enrichissement et Sauvegarde --- 
        logger.info(f"[Scan {scan_id}] Enrichissement des résultats avec CVSS...")
        final_report_data, max_score = enrich_findings_with_cvss(final_report_data)
        logger.info(f"[Scan {scan_id}] Enrichissement terminé. Score max: {max_score}")

        final_report_json = json.dumps(final_report_data, indent=2)
        report = Report.query.filter_by(scan_id=scan_id).first()
        if report:
            report.content = final_report_json
            report.generated_at = datetime.utcnow()
        else:
            report = Report(scan_id=scan_id, content=final_report_json, format="json", generated_at=datetime.utcnow())
            db.session.add(report)
        
        scan_history.status = overall_status
        scan_history.vulnerability_score = max_score
        scan_history.scan_end_time = datetime.utcnow()
        db.session.commit()
        logger.info(f"[Scan {scan_id}] Scan terminé. Statut final: {overall_status}, Score: {max_score}")

    except Exception as exc:
        logger.error(f"[Scan {scan_id}] Erreur majeure inattendue: {exc}", exc_info=True)
        if scan_history:
            try:
                scan_history.status = "failed"
                scan_history.scan_end_time = datetime.utcnow()
                if "errors" in final_report_data:
                     final_report_data["errors"].append(f"FATAL ERROR: {exc}")
                     report = Report.query.filter_by(scan_id=scan_id).first()
                     if report:
                         report.content = json.dumps(final_report_data, indent=2)
                     else:
                         report = Report(scan_id=scan_id, content=json.dumps(final_report_data, indent=2), format="json")
                         db.session.add(report)
                db.session.commit()
            except Exception as db_err:
                logger.error(f"[Scan {scan_id}] Erreur lors de la mise à jour du statut en \"failed\": {db_err}")
                db.session.rollback()
        self.retry(exc=exc)
    finally:
        # Nettoyage optionnel du répertoire de résultats ?
        # import shutil
        # if os.path.exists(result_dir):
        #     shutil.rmtree(result_dir)
        pass

