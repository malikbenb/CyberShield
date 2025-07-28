# Système de Pentesting Éthique Automatisé

Ce projet implémente un système de pentesting éthique automatisé composé de trois composants principaux :
1. Un client léger exécuté sur la machine cible avec des privilèges administrateur/root
2. Une API de pentesting qui orchestre les tests
3. Une infrastructure Docker qui héberge les outils de pentesting

## Architecture du système

Le système fonctionne selon l'architecture suivante :

```
┌─────────────────┐     HTTPS     ┌─────────────────┐     API interne    ┌─────────────────────────┐
│                 │  Sécurisé &   │                 │    orchestration   │  Infrastructure Docker   │
│  Client léger   │◄──────────────►│  API Pentesting │◄───────────────────►│                         │
│ (sur machine    │  Authentifié  │                 │                    │  ┌─────────┐ ┌─────────┐ │
│   cible)        │               │                 │                    │  │ Nmap    │ │Metasploit│ │
└─────────────────┘               └─────────────────┘                    │  │Container│ │Container │ │
                                                                         │  └─────────┘ └─────────┘ │
                                                                         │                         │
                                                                         │  ┌─────────┐ ┌─────────┐ │
                                                                         │  │ SQLMap  │ │Autres   │ │
                                                                         │  │         │ │Outils   │ │
                                                                         │  └─────────┘ └─────────┘ │
                                                                         └─────────────────────────┘
```

## Prérequis

- Python 3.10 ou supérieur
- Docker et Docker Compose
- Privilèges administrateur/root sur la machine cible

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/pentesting-project.git
cd pentesting-project
```

### 2. Configurer l'environnement virtuel Python

```bash
python3 -m venv venv
source venv/bin/activate  # Sur Linux/macOS
# ou
venv\Scripts\activate     # Sur Windows
pip install -r requirements.txt
```

### 3. Démarrer l'infrastructure Docker

```bash
cd docker
chmod +x start.sh
./start.sh
```

### 4. Configurer le client léger

```bash
cd docker
chmod +x setup_client.sh
./setup_client.sh
```

## Utilisation

### Exécuter le client léger

Le client léger doit être exécuté avec des privilèges administrateur/root sur la machine cible :

```bash
cd client
sudo python3 client.py --api http://adresse-ip-api:8000
```

Le client effectuera les étapes suivantes :
1. Affichage du document d'autorisation
2. Collecte des informations système
3. Connexion à l'API
4. Exécution des commandes de pentesting
5. Génération et téléchargement du rapport final

### Phases du test de pentesting

Le système effectue les phases suivantes de manière séquentielle :

1. **Reconnaissance** : Collecte d'informations sur le système
2. **Énumération** : Identification des services et ports ouverts
3. **Recherche de vulnérabilités** : Analyse des faiblesses potentielles
4. **Exploitation** : Vérification des vulnérabilités (sans exploitation destructive)
5. **Élévation de privilèges** : Recherche de possibilités d'élévation de privilèges
6. **Nettoyage** : Suppression des artefacts temporaires
7. **Génération du rapport** : Création d'un rapport détaillé avec recommandations

### Format du rapport

Le rapport final est disponible en deux formats :
- HTML : Pour une visualisation dans un navigateur
- PDF : Pour l'impression ou le partage

Le rapport contient les sections suivantes :
- Synthèse technique avec liste des vulnérabilités et impact dans le contexte métier
- Préconisations de remédiations
- Synthèse managériale
- Plan d'action avec macro-planning tenant compte du ROI sécurité

## Structure du projet

```
pentesting_project/
├── client/                 # Client léger
│   ├── client.py           # Script principal du client
│   └── config/             # Configuration du client
├── api/                    # API de pentesting
│   ├── api.py              # Script principal de l'API
│   ├── Dockerfile          # Dockerfile pour l'API
│   └── requirements.txt    # Dépendances Python pour l'API
├── docker/                 # Infrastructure Docker
│   ├── docker-compose.yml  # Configuration des services Docker
│   ├── start.sh            # Script de démarrage
│   ├── stop.sh             # Script d'arrêt
│   ├── setup_client.sh     # Script de configuration du client
│   └── test_integration.sh # Script de test d'intégration
├── tests/                  # Tests unitaires
│   ├── test_client.py      # Tests pour le client léger
│   └── test_api.py         # Tests pour l'API
├── reports/                # Rapports générés
└── results/                # Résultats des scans
```

## Composants détaillés

### Client léger

Le client léger est un script Python qui s'exécute sur la machine cible avec des privilèges administrateur/root. Il collecte des informations système, communique avec l'API de pentesting, exécute des commandes et récupère le rapport final.

Fonctionnalités principales :
- Vérification des privilèges administrateur/root
- Collecte d'informations système (adresse IP, nom de domaine, adresse MAC, DNS)
- Affichage d'un document d'autorisation
- Communication sécurisée avec l'API
- Exécution de commandes à distance
- Téléchargement du rapport final

### API de pentesting

L'API de pentesting est développée avec FastAPI et orchestre le processus de pentesting. Elle gère l'authentification, planifie les commandes à exécuter, analyse les résultats et génère les rapports.

Fonctionnalités principales :
- Authentification par JWT
- Orchestration du processus de pentesting
- Planification des commandes
- Analyse des résultats
- Génération de rapports en HTML et PDF

### Infrastructure Docker

L'infrastructure Docker héberge les outils de pentesting dans des conteneurs isolés. Elle comprend les services suivants :
- API de pentesting
- Nmap pour la découverte réseau
- Metasploit pour la vérification des vulnérabilités
- SQLMap pour les tests d'injection SQL

## Sécurité

Le système intègre plusieurs mesures de sécurité :
- Communication chiffrée entre le client et l'API
- Authentification par JWT
- Isolation des outils dans des conteneurs Docker
- Tests limités à la machine locale uniquement
- Autorisation explicite requise avant le début du scan

## Limitations

- Le système est limité à la machine locale uniquement
- Certaines fonctionnalités peuvent être bloquées par des pare-feu ou antivirus
- Les tests sont non destructifs et ne tentent pas d'exploiter réellement les vulnérabilités

## Dépannage

### L'API n'est pas accessible

Vérifiez que l'infrastructure Docker est en cours d'exécution :
```bash
cd docker
docker-compose ps
```

Si nécessaire, redémarrez l'infrastructure :
```bash
./stop.sh
./start.sh
```

### Le client ne peut pas se connecter à l'API

Vérifiez que l'URL de l'API est correcte et que le pare-feu autorise la connexion :
```bash
curl http://adresse-ip-api:8000
```

### Erreurs lors de l'exécution des commandes

Vérifiez que le client est exécuté avec des privilèges administrateur/root :
```bash
sudo python3 client.py --api http://adresse-ip-api:8000
```

## Licence

Ce projet est distribué sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Avertissement

Ce système est conçu pour des tests de pentesting éthiques uniquement. L'utilisation de ce système pour des tests non autorisés est illégale et contraire à l'éthique. Assurez-vous d'avoir l'autorisation explicite avant d'effectuer des tests sur un système.
