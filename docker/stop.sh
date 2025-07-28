#!/bin/bash
# Script d'arrêt pour l'infrastructure Docker

echo "Arrêt des services Docker..."

# S'assurer que le script est exécuté depuis le dossier docker/
cd "$(dirname "$0")"

# Vérifier si Docker Compose est installé (v1 ou v2)
if ! command -v docker-compose &> /dev/null
then
    if ! docker compose version &> /dev/null
    then
        echo "Avertissement : Docker Compose (v1 ou v2) ne semble pas installé. Tentative d'arrêt direct des conteneurs."
        # Tenter d'arrêter les conteneurs par nom si possible (nécessite de connaître les noms)
        # docker stop api_container nmap_container metasploit_container sqlmap_container
        # docker rm api_container nmap_container metasploit_container sqlmap_container
        echo "Impossible d'arrêter proprement sans docker-compose. Veuillez arrêter les conteneurs manuellement."
        exit 1
    fi
    # Utiliser la nouvelle syntaxe
    docker compose down
else
    # Utiliser l'ancienne syntaxe
    docker-compose down
fi

if [ $? -eq 0 ]; then
  echo "Infrastructure Docker arrêtée avec succès."
else
  echo "Erreur lors de l'arrêt de l'infrastructure Docker."
fi

exit 0

