#!/bin/bash
# Script de démarrage pour l'infrastructure Docker

echo "Démarrage des services Docker..."

# S'assurer que le script est exécuté depuis le dossier docker/
cd "$(dirname "$0")"

# Vérifier si Docker et Docker Compose sont installés
if ! command -v docker &> /dev/null
then
    echo "Erreur : Docker n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

if ! command -v docker-compose &> /dev/null
then
    # Essayer avec docker compose (nouvelle syntaxe)
    if ! docker compose version &> /dev/null
    then
        echo "Erreur : Docker Compose (v1 ou v2) n'est pas installé. Veuillez l'installer avant de continuer."
        exit 1
    fi
    # Utiliser la nouvelle syntaxe
    docker compose up -d --build
else
    # Utiliser l'ancienne syntaxe
    docker-compose up -d --build
fi

if [ $? -eq 0 ]; then
  echo "Infrastructure Docker démarrée avec succès."
else
  echo "Erreur lors du démarrage de l'infrastructure Docker."
  exit 1
fi

# Attendre un peu que les services démarrent (optionnel)
sleep 5

echo "Vérification de l'état des conteneurs :"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

exit 0

