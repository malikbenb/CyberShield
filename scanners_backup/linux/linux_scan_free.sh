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
    timeout 1 bash -c "echo >/dev/tcp/localhost/$1" 2>/dev/null && echo "Ouvert" || \
    (timeout 1 bash -c "echo >/dev/udp/localhost/$1" 2>/dev/null && echo "Filtré" || echo "Fermé")
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
progress 1 "Démarrage du scan Linux..."
progress 2 "Collecte des informations système..."

HOSTNAME=$(hostname)
OS_INFO=$(lsb_release -d 2>/dev/null | cut -f2-)
[ -z "$OS_INFO" ] && OS_INFO="$(cat /etc/*release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"')"
KERNEL=$(uname -r)
ARCH=$(uname -m)

progress 3 "Analyse réseau..."
LOCAL_IP=$(hostname -I 2>/dev/null || ip addr show 2>/dev/null | grep -w inet | grep -v 127.0.0.1 | awk '{print $2}' | cut -d/ -f1 | head -n1)
IPV6_ADDR=$(ip -6 addr show 2>/dev/null | grep global | awk '{print $2}' | head -n1 || echo "non_disponible")
MAC_ADDR=$(ip link show 2>/dev/null | grep ether | awk '{print $2}' | head -n1 || echo "non_disponible")
PUBLIC_IP=$(curl -s ifconfig.me --connect-timeout 3 || echo "non_disponible")
DNS_SERVERS=$(grep nameserver /etc/resolv.conf 2>/dev/null | awk '{print $2}' | tr '\n' ',' | sed 's/,$//')

progress 4 "Vérification du firewall..."

FW_STATUS="inactif"
FW_SYSTEM="aucun"
FW_RULES=""

# Détection du système de pare-feu
if command -v iptables &>/dev/null && sudo iptables -L -n 2>/dev/null | grep -q -v "Chain INPUT (policy ACCEPT)"; then
    FW_SYSTEM="iptables"
    FW_STATUS="actif"
    FW_RULES=$(sudo iptables-save 2>/dev/null | wc -l)
elif command -v nft &>/dev/null && sudo nft list ruleset 2>/dev/null | grep -q "hook input"; then
    FW_SYSTEM="nftables"
    FW_STATUS="actif"
    FW_RULES=$(sudo nft list ruleset 2>/dev/null | wc -l)
elif command -v ufw &>/dev/null && sudo ufw status 2>/dev/null | grep -q "Status: active"; then
    FW_SYSTEM="ufw"
    FW_STATUS="actif"
    FW_RULES=$(sudo ufw status numbered 2>/dev/null | wc -l)
elif command -v firewall-cmd &>/dev/null && sudo firewall-cmd --state 2>/dev/null | grep -q "running"; then
    FW_SYSTEM="firewalld"
    FW_STATUS="actif"
    FW_RULES=$(sudo firewall-cmd --list-all 2>/dev/null | wc -l)
fi

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
[[ $KERNEL == *"4.15"* ]] && VULNS+=("CVE-SIM-101:Noyau Linux 4.15 vulnérable:Critique:Mettre à jour le noyau")
[[ $(ss -tuln | grep ":445 ") ]] && VULNS+=("CVE-SIM-102:Port SMB 445 ouvert:Critique:Désactiver SMB")

progress 7 "Génération du rapport..."

# Génération du rapport texte
{
    echo "$CYBERSHIELD_ART"
    echo ""
    echo "================================================"
    echo " CYBERSHIELD ALGERIA - RAPPORT DE SCAN LINUX"
    echo "================================================"
    echo " Généré le : $TIMESTAMP"
    echo ""
    
    echo "1. INFORMATIONS SYSTÈME"
    echo "-----------------------"
    echo "Nom d'hôte : $HOSTNAME"
    echo "Système d'exploitation : $OS_INFO"
    echo "Noyau Linux : $KERNEL"
    echo "Architecture : $ARCH"
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
    echo "Système de pare-feu : $FW_SYSTEM"
    echo "État du pare-feu : $FW_STATUS"
    [ -n "$FW_RULES" ] && echo "Nombre de règles : $FW_RULES"
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
    if [ "$FW_STATUS" == "actif" ]; then
        echo ""
        echo "6. RÈGLES DE PARE-FEU ($FW_SYSTEM)"
        echo "---------------------------------"
        case $FW_SYSTEM in
            iptables)
                sudo iptables -L -n 2>/dev/null
                ;;
            nftables)
                sudo nft list ruleset 2>/dev/null
                ;;
            ufw)
                sudo ufw status numbered 2>/dev/null
                ;;
            firewalld)
                sudo firewall-cmd --list-all 2>/dev/null
                ;;
        esac
    fi
} > "$REPORT_PATH"

progress 8 "Scan terminé !"
echo ""
echo "Rapport généré : $REPORT_PATH"
echo ""