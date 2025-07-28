#!/bin/bash

# Configuration
REPORT_PATH="$HOME/CyberShield_Scan_Report_$(date +'%Y%m%d_%H%M%S').txt"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# ASCII Art Header
CYBERSHIELD_ART=$(cat << "EOF"
   ______      __              _____ __    _      __    __   ___    __                _      
  / ____/_  __/ /_  ___  _____/ ___// /_  (_)__  / /___/ /  /   |  / /___ ____  _____(_)___ _
 / /   / / / / __ \/ _ \/ ___/\__ \/ __ \/ / _ \/ / __  /  / /| | / / __ `/ _ \/ ___/ / __ `/
/ /___/ /_/ / /_/ /  __/ /   ___/ / / / / /  __/ / /_/ /  / ___ |/ / /_/ /  __/ /  / / /_/ / 
\____/\__, /_.___/\___/_/   /____/_/ /_/_/\___/_/\__,_/  /_/  |_/_/\__, /\___/_/  /_/\__,_/  
     /____/                                                       /____/                     
EOF
)

# Fonctions utilitaires
progress() {
    echo "[$(date +'%H:%M:%S')] [$1/8] $2"
}

test_port() {
    nc -z -G 1 localhost $1 &>/dev/null && echo "Ouvert" || \
    (nc -z -u -G 1 localhost $1 &>/dev/null && echo "Filtré" || echo "Fermé")
}

# Fonction pour obtenir la version du service
get_service_version() {
    case $1 in
        21)   echo "FTP" ;;
        22)   ssh -V 2>&1 | cut -d' ' -f1 | cut -d'_' -f1 ;;
        80)   curl -sI http://localhost 2>/dev/null | grep -i 'Server:' | cut -d' ' -f2- | tr -d '\r\n' || echo "N/A" ;;
        443)  curl -sI https://localhost 2>/dev/null | grep -i 'Server:' | cut -d' ' -f2- | tr -d '\r\n' || echo "N/A" ;;
        445)  echo "SMB" ;;
        3389) echo "RDP" ;;
        *)    echo "N/A" ;;
    esac
}

# Scan principal
progress 1 "Démarrage du scan macOS..."
progress 2 "Collecte des informations système..."

HOSTNAME=$(scutil --get ComputerName 2>/dev/null || hostname)
OS_INFO=$(sw_vers -productName)
OS_VERSION=$(sw_vers -productVersion)
HARDWARE=$(sysctl -n hw.model)

progress 3 "Analyse réseau..."
LOCAL_IP=$(ifconfig | grep -w inet | grep -v 127.0.0.1 | awk '{print $2}' | head -n1)
IPV6_ADDR=$(ifconfig | grep inet6 | grep -v fe80:: | awk '{print $2}' | head -n1 || echo "non_disponible")
MAC_ADDR=$(ifconfig en0 | grep ether | awk '{print $2}' || ifconfig | grep ether | head -n1 | awk '{print $2}' || echo "non_disponible")
PUBLIC_IP=$(curl -s ifconfig.me --connect-timeout 3 || echo "non_disponible")
DNS_SERVERS=$(scutil --dns 2>/dev/null | grep nameserver | awk '{print $3}' | sort | uniq | tr '\n' ',' | sed 's/,$//')

progress 4 "Vérification du firewall..."

# Vérification du pare-feu PF
PF_STATUS=$(sudo pfctl -si 2>/dev/null | grep "Status" | awk '{print $2}')
PF_RULES=""
if [ "$PF_STATUS" == "Enabled" ]; then
    FW_STATUS="actif (pf)"
    PF_RULES=$(sudo pfctl -sr 2>/dev/null)
else
    FW_STATUS="inactif (pf)"
fi

# Vérification de l'application firewall
APPFW_STATUS=$(sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | awk '{print $1}')
APPFW_RULES=$(sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps 2>/dev/null | grep -E '(ALF|enabled)')

progress 5 "Scan des ports..."
PORTS_TO_SCAN="21 22 80 443 445 3389"
PORT_RESULTS=()
for port in $PORTS_TO_SCAN; do
    status=$(test_port $port)
    service=""
    version=$(get_service_version $port)
    case $port in
        21)   service="FTP" ;;
        22)   service="SSH" ;;
        80)   service="HTTP" ;;
        443)  service="HTTPS" ;;
        445)  service="SMB" ;;
        3389) service="RDP" ;;
    esac

    # Détermination de la sévérité
    severity=""
    case $status in
        "Ouvert")   severity="Élevée" ;;
        "Filtré")   severity="Moyenne" ;;
        "Fermé")    severity="Faible" ;;
        *)          severity="Inconnue" ;;
    esac

    PORT_RESULTS+=("$port:$service:$version:$status:$severity")
done

progress 6 "Détection des vulnérabilités..."
VULNS=()
[[ $OS_VERSION == *"10.15"* ]] && VULNS+=("CVE-SIM-201:macOS Catalina 10.15 vulnérable:Critique:Mettre à jour le système")
[[ $(netstat -an | grep ".445 ") ]] && VULNS+=("CVE-SIM-202:Port SMB 445 ouvert:Critique:Désactiver SMB")

progress 7 "Génération du rapport..."

# Génération du rapport texte
{
    echo "$CYBERSHIELD_ART"
    echo ""
    echo "================================================"
    echo " CYBERSHIELD ALGERIA - RAPPORT DE SCAN macOS"
    echo "================================================"
    echo " Généré le : $TIMESTAMP"
    echo ""
    
    echo "1. INFORMATIONS SYSTÈME"
    echo "-----------------------"
    echo "Nom d'hôte : $HOSTNAME"
    echo "Système d'exploitation : $OS_INFO $OS_VERSION"
    echo "Modèle matériel : $HARDWARE"
    echo ""
    
    echo "2. INFORMATIONS RÉSEAU"
    echo "----------------------"
    echo "IP Locale : $LOCAL_IP"
    echo "IPv6 : $IPV6_ADDR"
    echo "Adresse MAC : $MAC_ADDR"
    echo "IP Publique : $PUBLIC_IP"
    echo "Serveurs DNS : $DNS_SERVERS"
    echo ""
    
    echo "3. CONFIGURATION DE SÉCURITÉ"
    echo "----------------------------"
    echo "Pare-feu PF : $FW_STATUS"
    echo "Firewall applicatif : $APPFW_STATUS"
    echo ""
    
    echo "4. RÉSULTATS DU SCAN DE PORTS"
    echo "-----------------------------"
    printf "%-6s %-8s %-15s %-8s %-10s\n" "PORT" "SERVICE" "VERSION" "STATUT" "SÉVÉRITÉ"
    for result in "${PORT_RESULTS[@]}"; do
        IFS=':' read -r port service version status severity <<< "$result"
        printf "%-6s %-8s %-15s %-8s %-10s\n" "$port" "$service" "$version" "$status" "$severity"
    done
    echo ""
    
    if [ ${#VULNS[@]} -gt 0 ]; then
        echo "5. VULNÉRABILITÉS DÉTECTÉES"
        echo "--------------------------"
        printf "%-12s %-40s %-10s %-30s\n" "ID" "DESCRIPTION" "SÉVÉRITÉ" "SOLUTION"
        for vuln in "${VULNS[@]}"; do
            IFS=':' read -r id desc severity solution <<< "$vuln"
            printf "%-12s %-40s %-10s %-30s\n" "$id" "$desc" "$severity" "$solution"
        done
    else
        echo "5. AUCUNE VULNÉRABILITÉ CRITIQUE DÉTECTÉE"
        echo "----------------------------------------"
    fi
    
    # Ajout des règles de pare-feu si disponibles
    echo ""
    echo "6. RÈGLES DE PARE-FEU"
    echo "---------------------"
    if [ "$PF_STATUS" == "Enabled" ]; then
        echo "Règles PF (Packet Filter):"
        echo "$PF_RULES"
        echo ""
    fi
    
    if [ -n "$APPFW_RULES" ]; then
        echo "Règles du Firewall Applicatif:"
        echo "$APPFW_RULES"
    fi
} > "$REPORT_PATH"

progress 8 "Scan terminé !"
echo ""
echo "Rapport généré : $REPORT_PATH"
echo ""