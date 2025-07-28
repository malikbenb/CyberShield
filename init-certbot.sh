#!/bin/bash

# Script d'initialisation pour Certbot
# Ce script génère les certificats SSL initiaux pour le domaine cybershield-algeria.com

# Vérifier si le répertoire certbot existe
if [ ! -d "/home/ubuntu/cybershield/cybershield_plateforme_complete/certbot" ]; then
  mkdir -p /home/ubuntu/cybershield/cybershield_plateforme_complete/certbot/conf
  mkdir -p /home/ubuntu/cybershield/cybershield_plateforme_complete/certbot/www
fi

# Créer le fichier .htpasswd pour l'accès à Prometheus
if [ ! -f "/home/ubuntu/cybershield/cybershield_plateforme_complete/.htpasswd" ]; then
  echo "Création du fichier .htpasswd pour l'accès à Prometheus"
  # Génération du mot de passe pour l'utilisateur admin (mot de passe: cybershield2025)
  echo "admin:$(openssl passwd -apr1 cybershield2025)" > /home/ubuntu/cybershield/cybershield_plateforme_complete/.htpasswd
fi

# Arrêter les conteneurs existants
echo "Arrêt des conteneurs existants..."
cd /home/ubuntu/cybershield/cybershield_plateforme_complete
docker-compose down

# Démarrer Nginx pour le challenge Certbot
echo "Démarrage de Nginx pour le challenge Certbot..."
docker-compose up -d nginx

# Attendre que Nginx soit prêt
echo "Attente du démarrage de Nginx..."
sleep 5

# Exécuter Certbot pour obtenir les certificats
echo "Obtention des certificats SSL avec Certbot..."
docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot \
  --email admin@cybershield-algeria.com --agree-tos --no-eff-email \
  -d cybershield-algeria.com -d www.cybershield-algeria.com

# Redémarrer tous les services
echo "Redémarrage de tous les services avec SSL activé..."
docker-compose down
docker-compose up -d

echo "Configuration HTTPS terminée. Votre site est maintenant accessible en HTTPS."
echo "Les certificats seront automatiquement renouvelés tous les 60 jours."
