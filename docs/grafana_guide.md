# Guide d'utilisation de Grafana pour CyberShield

## Introduction

Grafana est un outil de visualisation et de monitoring qui vous permet de surveiller les performances et l'utilisation de votre plateforme CyberShield. Ce guide vous explique comment accéder à Grafana et utiliser les tableaux de bord disponibles.

## Accès à Grafana

1. **URL d'accès**: Grafana est accessible à l'adresse suivante: `http://votre-domaine:3000` ou via le lien dans l'interface d'administration.

2. **Identifiants de connexion**:
   - Nom d'utilisateur: `admin`
   - Mot de passe: `cybershield2025`

   Nous vous recommandons de changer ce mot de passe après votre première connexion.

## Tableaux de bord disponibles

### Tableau de bord principal

Le tableau de bord principal vous donne une vue d'ensemble des performances et de l'utilisation de la plateforme CyberShield. Il est divisé en plusieurs sections:

1. **Vue d'ensemble du système**:
   - Utilisation CPU
   - Utilisation mémoire

2. **Métriques API**:
   - Requêtes par seconde
   - Codes de statut HTTP

3. **Métriques des scans**:
   - Nombre total de scans
   - Scans en cours
   - Scans échoués
   - Durée moyenne des scans

## Interprétation des métriques

### Utilisation CPU et mémoire

Ces graphiques montrent l'utilisation des ressources système au fil du temps. Des pics soudains ou une utilisation constamment élevée peuvent indiquer des problèmes de performance.

### Requêtes API

Le graphique des requêtes par seconde montre le trafic sur votre API. Les pics peuvent correspondre à des périodes de forte activité.

### Codes de statut HTTP

Ce graphique montre la répartition des codes de statut HTTP:
- 2xx: Requêtes réussies
- 4xx: Erreurs client (ex: authentification échouée)
- 5xx: Erreurs serveur (problèmes internes)

Un nombre élevé d'erreurs 5xx nécessite une attention immédiate.

### Métriques des scans

- **Nombre total de scans**: Cumul de tous les scans effectués
- **Scans en cours**: Nombre de scans actuellement en exécution
- **Scans échoués**: Nombre de scans qui ont échoué
- **Durée moyenne**: Temps moyen nécessaire pour compléter un scan

## Alertes

Des alertes sont configurées pour vous notifier en cas de problèmes:
- Utilisation CPU > 80%
- Utilisation mémoire > 80%
- Taux d'erreurs API > 5%
- Échecs de scans consécutifs > 3

Les notifications sont envoyées à l'adresse email configurée dans les paramètres d'administration.

## Personnalisation

Vous pouvez personnaliser les tableaux de bord existants ou en créer de nouveaux:

1. Pour modifier un tableau de bord, cliquez sur l'icône d'engrenage en haut à droite
2. Pour créer un nouveau tableau de bord, cliquez sur "+" dans le menu latéral puis "Dashboard"
3. Pour ajouter un panneau, cliquez sur "Add panel"

## Support

Si vous avez des questions sur l'utilisation de Grafana ou si vous rencontrez des problèmes, contactez notre équipe de support à support@cybershield-algeria.com.
