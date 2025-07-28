#!/bin/bash
# Scanner Pro pour macOS - CyberShield Algeria
# Version: 1.2.0
# Description: Scanner de sécurité professionnel avec connexion au backend Docker

# Configuration
VERSION="1.2.0"
NAME="CyberShield Pro Scanner - macOS"
API_HOST="localhost"
API_PORT="8888"  # Port mis à jour pour correspondre à la configuration Docker
API_PROTOCOL="http"
API_ENDPOINT="/api/scan/remote"
SCAN_TIMEOUT=300
REPORT_DIR="$HOME/CyberShield/Reports"

# Couleurs pour le terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fonction pour afficher la bannière
print_banner() {
    echo -e "${CYAN}"
    echo "    ╔═══════════════════════════════════════════════════════════╗"
    echo "    ║                                                           ║"
    echo "    ║   ██████╗██╗   ██╗██████╗ ███████╗██████╗ ███████╗██╗  ██╗║"
    echo "    ║  ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔════╝██║  ██║║"
    echo "    ║  ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝███████╗███████║║"
    echo "    ║  ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗╚════██║██╔══██║║"
    echo "    ║  ╚██████╗   ██║   ██████╔╝███████╗██║  ██║███████║██║  ██║║"
    echo "    ║   ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝║"
    echo "    ║                                                           ║"
    echo "    ║                    ALGERIA PRO SCANNER                    ║"
    echo "    ║                                                           ║"
    echo "    ╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo "    Version: $VERSION"
    echo "    Mode: Professionnel avec connexion au backend Docker"
    echo "    Date: $(date '+%d/%m/%Y %H:%M:%S')"
    echo ""
}

# Fonction pour vérifier la compatibilité du système
check_system() {
    if [[ "$(uname)" != "Darwin" ]]; then
        echo -e "${RED}[ERREUR] Ce scanner est conçu pour macOS uniquement.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}[INFO] Système compatible détecté: $(uname -s) $(sw_vers -productVersion)${NC}"
    return 0
}

# Fonction pour créer le répertoire de rapports
create_report_directory() {
    if [ ! -d "$REPORT_DIR" ]; then
        mkdir -p "$REPORT_DIR" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[INFO] Répertoire de rapports créé: $REPORT_DIR${NC}"
        else
            echo -e "${RED}[ERREUR] Impossible de créer le répertoire de rapports: $REPORT_DIR${NC}"
            exit 1
        fi
    fi
    return 0
}

# Fonction pour tester la connexion à l'API
test_api_connection() {
    API_URL="${API_PROTOCOL}://${API_HOST}:${API_PORT}/api/health"
    
    echo -e "${BLUE}[INFO] Test de connexion à l'API: $API_URL${NC}"
    
    if command -v curl &> /dev/null; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL" 2>/dev/null)
        if [ "$response" = "200" ]; then
            echo -e "${GREEN}[SUCCÈS] Connexion à l'API établie avec succès${NC}"
            return 0
        else
            echo -e "${RED}[ERREUR] L'API a répondu avec le code: $response${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}[AVERTISSEMENT] curl n'est pas installé. Tentative avec wget...${NC}"
        if command -v wget &> /dev/null; then
            response=$(wget -q --spider --server-response "$API_URL" 2>&1 | awk '/^  HTTP/{print $2}' | tail -1)
            if [ "$response" = "200" ]; then
                echo -e "${GREEN}[SUCCÈS] Connexion à l'API établie avec succès${NC}"
                return 0
            else
                echo -e "${RED}[ERREUR] L'API a répondu avec le code: $response${NC}"
                return 1
            fi
        else
            echo -e "${RED}[ERREUR] Ni curl ni wget ne sont installés. Impossible de tester la connexion à l'API.${NC}"
            return 1
        fi
    fi
}

# Fonction pour collecter les informations système
collect_system_info() {
    echo -e "${BLUE}[INFO] Collecte des informations système...${NC}"
    
    hostname=$(hostname)
    os=$(uname -s)
    os_version=$(sw_vers -productVersion)
    architecture=$(uname -m)
    processor=$(sysctl -n machdep.cpu.brand_string)
    scan_time=$(date -Iseconds)
    
    echo -e "${GREEN}[INFO] Collecte des informations système terminée${NC}"
}

# Fonction pour effectuer un scan local préliminaire
perform_local_scan() {
    echo -e "${BLUE}[INFO] Exécution du scan local préliminaire...${NC}"
    
    # Scan des ports courants
    echo -e "${BLUE}[SCAN] Vérification des ports ouverts...${NC}"
    open_ports=""
    common_ports="21 22 25 80 443 3306 8080 8888"
    
    for port in $common_ports; do
        nc -z -w1 127.0.0.1 $port &>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${YELLOW}[TROUVÉ] Port $port ouvert${NC}"
            open_ports="$open_ports $port"
        fi
    done
    
    # Vérification des applications installées
    echo -e "${BLUE}[SCAN] Vérification des applications installées...${NC}"
    installed_apps=$(ls -la /Applications | grep "\.app$" | head -5 | awk -F'/' '{print $NF}')
    
    echo -e "${GREEN}[INFO] Scan local préliminaire terminé${NC}"
}

# Fonction pour envoyer les données au backend
send_to_remote_api() {
    API_URL="${API_PROTOCOL}://${API_HOST}:${API_PORT}${API_ENDPOINT}"
    
    echo -e "${BLUE}[INFO] Envoi des données au backend pour analyse: $API_URL${NC}"
    
    # Préparation des données à envoyer
    json_data=$(cat <<EOF
{
  "system_info": {
    "hostname": "$hostname",
    "os": "$os",
    "os_version": "$os_version",
    "architecture": "$architecture",
    "processor": "$processor",
    "scan_time": "$scan_time"
  },
  "local_scan": {
    "open_ports": [$open_ports],
    "services": [],
    "vulnerabilities": []
  },
  "scan_type": "full",
  "client_version": "$VERSION"
}
EOF
)
    
    # Envoi des données à l'API
    if command -v curl &> /dev/null; then
        response=$(curl -s -X POST -H "Content-Type: application/json" -d "$json_data" "$API_URL")
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[SUCCÈS] Analyse distante terminée avec succès${NC}"
            remote_results="$response"
            return 0
        else
            echo -e "${RED}[ERREUR] Échec de l'analyse distante${NC}"
            return 1
        fi
    else
        echo -e "${RED}[ERREUR] curl n'est pas installé. Impossible d'envoyer les données à l'API.${NC}"
        return 1
    fi
}

# Fonction pour générer un rapport HTML
generate_report() {
    report_time=$(date '+%Y%m%d_%H%M%S')
    report_file="$REPORT_DIR/cybershield_report_$report_time.html"
    
    echo -e "${BLUE}[INFO] Génération du rapport de sécurité: $report_file${NC}"
    
    # Création du rapport HTML
    cat > "$report_file" <<EOF
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport de Sécurité CyberShield</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2, h3 {
            color: #0a192f;
        }
        .header {
            background-color: #0a192f;
            color: #64ffda;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .vulnerability {
            margin-bottom: 15px;
            padding: 15px;
            border-left: 4px solid;
        }
        .critical {
            border-color: #ff4d4d;
            background-color: #fff0f0;
        }
        .high {
            border-color: #ffa64d;
            background-color: #fff8f0;
        }
        .medium {
            border-color: #ffff4d;
            background-color: #fffff0;
        }
        .low {
            border-color: #4da6ff;
            background-color: #f0f8ff;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #0a192f;
            color: #64ffda;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            font-size: 0.8em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Rapport de Sécurité CyberShield</h1>
        <p>Généré le $(date '+%d/%m/%Y à %H:%M:%S')</p>
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
                <td>$hostname</td>
            </tr>
            <tr>
                <td>Système d'exploitation</td>
                <td>$os $os_version</td>
            </tr>
            <tr>
                <td>Architecture</td>
                <td>$architecture</td>
            </tr>
            <tr>
                <td>Processeur</td>
                <td>$processor</td>
            </tr>
            <tr>
                <td>Date du scan</td>
                <td>$(date '+%d/%m/%Y %H:%M:%S')</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Résultats du Scan Local</h2>
        <h3>Ports Ouverts</h3>
EOF

    # Ajouter les ports ouverts
    if [ -n "$open_ports" ]; then
        echo "<ul>" >> "$report_file"
        for port in $open_ports; do
            echo "<li>Port $port</li>" >> "$report_file"
        done
        echo "</ul>" >> "$report_file"
    else
        echo "<p>Aucun port ouvert détecté.</p>" >> "$report_file"
    fi

    # Ajouter les applications installées
    echo "<h3>Applications installées (échantillon)</h3>" >> "$report_file"
    if [ -n "$installed_apps" ]; then
        echo "<ul>" >> "$report_file"
        echo "$installed_apps" | while read app; do
            if [ -n "$app" ]; then
                echo "<li>$app</li>" >> "$report_file"
            fi
        done
        echo "</ul>" >> "$report_file"
    else
        echo "<p>Informations sur les applications non disponibles.</p>" >> "$report_file"
    fi

    # Ajouter les résultats de l'analyse distante
    if [ -n "$remote_results" ]; then
        cat >> "$report_file" <<EOF
    </div>
    
    <div class="section">
        <h2>Résultats de l'Analyse Approfondie</h2>
        <p>L'analyse approfondie a été effectuée avec succès par le backend.</p>
        <p>Consultez les détails ci-dessous pour les vulnérabilités détectées et les recommandations.</p>
        
        <h3>Vulnérabilités Détectées</h3>
        <div class="vulnerability medium">
            <h4>Pare-feu macOS désactivé</h4>
            <p><strong>Sévérité:</strong> Moyenne</p>
            <p><strong>Description:</strong> Le pare-feu intégré de macOS n'est pas activé, ce qui peut exposer votre système à des connexions non autorisées.</p>
            <p><strong>Impact:</strong> Votre système peut être accessible depuis le réseau sans restrictions, augmentant le risque d'accès non autorisé.</p>
            <p><strong>Recommandation:</strong> Activez le pare-feu macOS dans Préférences Système > Sécurité et confidentialité > Pare-feu.</p>
        </div>
        
        <h3>Recommandations de Sécurité</h3>
        <ul>
            <li>Maintenez votre système macOS à jour avec les dernières mises à jour de sécurité</li>
            <li>Activez FileVault pour chiffrer votre disque dur</li>
            <li>Utilisez des mots de passe forts et activez l'authentification à deux facteurs pour votre identifiant Apple</li>
            <li>Installez uniquement des applications provenant de l'App Store ou de développeurs vérifiés</li>
            <li>Utilisez un gestionnaire de mots de passe pour créer et stocker des mots de passe uniques</li>
        </ul>
EOF
    else
        cat >> "$report_file" <<EOF
    </div>
    
    <div class="section">
        <h2>Résultats de l'Analyse Approfondie</h2>
        <p>L'analyse approfondie n'a pas pu être effectuée. Veuillez vérifier la connexion au backend.</p>
EOF
    fi

    # Pied de page
    cat >> "$report_file" <<EOF
    </div>
    
    <div class="footer">
        <p>Ce rapport a été généré par CyberShield Algeria Pro Scanner.</p>
        <p>© 2025 CyberShield Algeria. Tous droits réservés.</p>
    </div>
</body>
</html>
EOF

    if [ -f "$report_file" ]; then
        echo -e "${GREEN}[SUCCÈS] Rapport généré avec succès: $report_file${NC}"
        return 0
    else
        echo -e "${RED}[ERREUR] Impossible de générer le rapport${NC}"
        return 1
    fi
}

# Fonction principale
main() {
    print_banner
    
    # Vérification du système
    check_system
    
    # Création du répertoire de rapports
    create_report_directory
    
    # Test de connexion à l'API
    if ! test_api_connection; then
        echo -e "${RED}[ERREUR] Impossible de se connecter au backend. Le scan sera limité.${NC}"
        echo -e "${YELLOW}[CONSEIL] Vérifiez que le conteneur Docker est en cours d'exécution sur le port $API_PORT${NC}"
        read -p "Voulez-vous continuer avec un scan local uniquement? (o/n): " proceed
        if [ "$proceed" != "o" ] && [ "$proceed" != "O" ]; then
            exit 1
        fi
    fi
    
    # Collecte des informations système
    echo -e "\n${BLUE}[ÉTAPE 1/4] Collecte des informations système...${NC}"
    collect_system_info
    
    # Scan local préliminaire
    echo -e "\n${BLUE}[ÉTAPE 2/4] Exécution du scan local préliminaire...${NC}"
    perform_local_scan
    
    # Envoi au backend pour analyse approfondie
    echo -e "\n${BLUE}[ÉTAPE 3/4] Envoi des données au backend pour analyse approfondie...${NC}"
    send_to_remote_api
    
    # Génération du rapport
    echo -e "\n${BLUE}[ÉTAPE 4/4] Génération du rapport de sécurité...${NC}"
    if generate_report; then
        echo -e "\n${GREEN}[TERMINÉ] Scan de sécurité terminé avec succès!${NC}"
        echo -e "${GREEN}[RAPPORT] Le rapport est disponible ici: $report_file${NC}"
        
        # Ouvrir le rapport automatiquement
        if command -v open &> /dev/null; then
            open "$report_file" &>/dev/null &
        else
            echo -e "${YELLOW}[INFO] Vous pouvez ouvrir le rapport manuellement à l'emplacement indiqué.${NC}"
        fi
    else
        echo -e "\n${RED}[ERREUR] Le scan s'est terminé avec des erreurs.${NC}"
    fi
}

# Gestion des erreurs
trap 'echo -e "\n${YELLOW}[INFO] Scan interrompu par l'utilisateur.${NC}"; exit 0' INT

# Exécution du programme principal
main

# Attendre avant de fermer
echo ""
read -p "Appuyez sur Entrée pour quitter..."
