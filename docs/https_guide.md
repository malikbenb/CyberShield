# Guide de configuration HTTPS pour CyberShield

## Introduction

Ce guide explique comment la sécurisation HTTPS a été mise en place pour la plateforme CyberShield et comment maintenir cette configuration.

## Configuration HTTPS

La plateforme CyberShield utilise Certbot (Let's Encrypt) pour obtenir et renouveler automatiquement les certificats SSL. Cette configuration assure que toutes les communications entre les utilisateurs et la plateforme sont chiffrées.

### Composants de la configuration HTTPS

1. **Certbot**: Service qui obtient et renouvelle automatiquement les certificats SSL de Let's Encrypt.
2. **Nginx**: Serveur web configuré pour utiliser les certificats SSL et rediriger tout le trafic HTTP vers HTTPS.
3. **Script d'initialisation**: `init-certbot.sh` qui facilite la configuration initiale des certificats.

## Fonctionnement

### Redirection automatique vers HTTPS

Tous les accès HTTP (port 80) sont automatiquement redirigés vers HTTPS (port 443). Cette redirection est configurée dans le fichier `nginx.conf`.

### Renouvellement automatique des certificats

Les certificats SSL de Let's Encrypt sont valides pendant 90 jours. Le service Certbot est configuré pour vérifier et renouveler automatiquement les certificats tous les 12 heures si nécessaire (généralement 30 jours avant l'expiration).

### Sécurité renforcée

La configuration HTTPS inclut:
- Protocoles TLS modernes (TLSv1.2, TLSv1.3)
- Suites de chiffrement sécurisées
- HSTS (HTTP Strict Transport Security)
- Protection contre le clickjacking (X-Frame-Options)
- Protection XSS (X-XSS-Protection)
- Protection MIME sniffing (X-Content-Type-Options)

## Maintenance

### Vérification des certificats

Pour vérifier l'état des certificats:

```bash
docker-compose exec certbot certbot certificates
```

### Renouvellement manuel des certificats

Si nécessaire, vous pouvez forcer le renouvellement des certificats:

```bash
docker-compose exec certbot certbot renew --force-renewal
```

### En cas de problème

Si vous rencontrez des problèmes avec les certificats:

1. Vérifiez que le domaine pointe correctement vers votre serveur
2. Vérifiez que les ports 80 et 443 sont ouverts sur votre pare-feu
3. Exécutez le script d'initialisation: `bash init-certbot.sh`

## Accès sécurisés

### API et Frontend

L'API et le frontend sont accessibles via HTTPS:
- Frontend: `https://cybershield-algeria.com`
- API: `https://cybershield-algeria.com/api`

### Grafana

Grafana est accessible via HTTPS avec authentification:
- URL: `https://cybershield-algeria.com/grafana`
- Identifiants par défaut: voir le guide d'utilisation de Grafana

### Prometheus (Accès administrateur uniquement)

Prometheus est protégé par une authentification HTTP basique:
- URL: `https://cybershield-algeria.com/prometheus`
- Nom d'utilisateur: `admin`
- Mot de passe: `cybershield2025`

## Recommandations

- Ne partagez pas les identifiants d'accès à Prometheus
- Changez régulièrement les mots de passe d'accès
- Vérifiez périodiquement l'état des certificats
- Conservez une sauvegarde des certificats et clés privées
