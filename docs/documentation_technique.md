# Documentation Technique (Mise à Jour)

Ce document fournit une documentation technique détaillée du système de pentesting éthique automatisé refactorisé, destinée aux développeurs et administrateurs système.

## 1. Architecture Technique

### 1.1 Vue d'ensemble

Le système est basé sur une architecture microservices conteneurisée avec Docker, facilitant le déploiement, la scalabilité et la maintenance. Les composants principaux sont :

1.  **Frontend Unifié (FE)**: Interface web statique (HTML/CSS/JS) pour la présentation des offres et le téléchargement des scanners.
2.  **Reverse Proxy (Nginx)**: Point d'entrée unique, gère HTTPS, route les requêtes vers le frontend et l'API (REST et WebSocket).
3.  **API Backend (FastAPI)**: Cœur logique, gère la communication avec les agents via WebSocket (WSS), orchestre les scans via Celery, interagit avec la base de données.
4.  **Base de Données (PostgreSQL)**: Stockage persistant des informations clients, scans, tâches et résultats.
5.  **File d'Attente (Redis)**: Broker de messages pour découpler l'API des tâches longues exécutées par les workers.
6.  **Worker (Celery)**: Exécute les tâches de scan (ex: lancement d'outils conteneurisés) et de génération de rapports de manière asynchrone.
7.  **Agent Client (Python/WebSocket)**: Application légère exécutée sur la machine cible (Pro/Entreprise), communique avec l'API via WebSocket sécurisé (mTLS recommandé), exécute les commandes reçues.
8.  **Scanner Gratuit (Scripts Locaux)**: Scripts (PowerShell, Bash) exécutés localement sans connexion backend.
9.  **Outils de Scan (Dockerisés)**: Conteneurs Docker pour les outils de pentesting (Nmap, OpenVAS, Nuclei, etc.), lancés par les workers Celery.

### 1.2 Diagramme d'Architecture

```mermaid
graph TD
    User[Utilisateur] --> FE[Frontend Unifié (Web)]

    subgraph "Machine Client"
        ClientAgent[Agent Client (Pro/Entreprise)]
        ScannerFree[Scanner Gratuit (Local)]
    end

    subgraph "Serveur Dédié (Docker)"
        FE -- HTTPS --> Nginx[Reverse Proxy (Nginx)]
        Nginx -- /api --> API[API Backend (FastAPI)]
        Nginx -- /ws --> API # WebSocket pour Agent Client
        Nginx -- / --> FE_Static[Fichiers Frontend]

        API -- Stockage --> DB[(PostgreSQL)]
        API -- Tâches --> Queue[(Redis)]
        API -- Communication Sécurisée (WSS) --> ClientAgent

        Worker[Worker (Celery)] -- Lecture --> Queue
        Worker -- Exécution --> ScanningTools
        Worker -- Résultats --> API

        subgraph ScanningTools [Outils de Scan (Conteneurs)]
            Nmap
            Metasploit
            SQLMap
            OpenVAS[OpenVAS/GVM]
            Nikto
            Nuclei
            Autres[Autres...]
        end
    end

    FE -- Téléchargement --> ScannerFree
    FE -- Téléchargement --> ClientAgent

    ClientAgent -- Connexion Sécurisée (WebSocket + mTLS) --> API
    API -- Commandes --> ClientAgent
    ClientAgent -- Résultats --> API
```

## 2. Spécifications Techniques

### 2.1 Frontend Unifié

*   **Technologie**: HTML, CSS, JavaScript (basé sur `Test Incubateur/CyberShield-Local-V8/client`).
*   **Fonctionnalités**: Présentation des offres, téléchargement des scanners (gratuit et agent), informations générales.
*   **Déploiement**: Fichiers statiques servis par Nginx.

### 2.2 Reverse Proxy (Nginx)

*   **Configuration**: `nginx.conf`.
*   **Rôles**: Terminaison SSL/TLS, routage `/` vers frontend, `/api` vers API REST, `/ws` vers API WebSocket. Gestion mTLS (commentée, à activer).

### 2.3 API Backend (FastAPI)

*   **Fichier principal**: `api/main.py`.
*   **Framework**: FastAPI.
*   **Dépendances clés**: `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `redis`, `celery`, `websockets`, `python-jose` (pour JWT si espace client), `psycopg2-binary`.
*   **Points d'entrée principaux**:
    *   `POST /api/clients/register`: Enregistrement initial de l'agent.
    *   `POST /api/scans`: Initiation d'un nouveau scan pour un client.
    *   `WebSocket /ws/{client_uuid}`: Canal de communication principal avec l'agent (commandes, résultats, heartbeat).
*   **Communication Agent**: WebSocket sécurisé (WSS). L'authentification est prévue via mTLS (à configurer dans Nginx et vérifier dans l'API) ou un handshake basé sur token via le WebSocket.
*   **Orchestration**: Utilise Celery et Redis pour lancer des tâches de scan asynchrones (`run_scan_tool`).
*   **Base de données**: Utilise SQLAlchemy avec asyncpg pour interagir avec PostgreSQL (modèles définis dans `main.py`).

### 2.4 Base de Données (PostgreSQL)

*   **Rôle**: Persistance des données.
*   **Modèles**: `Client`, `Scan`, `ScanTask` (définis dans `api/main.py`).
*   **Configuration**: Via variables d'environnement (`.env` file) utilisées par `docker-compose.yml`.

### 2.5 File d'Attente (Redis) & Worker (Celery)

*   **Rôle**: Gestion des tâches asynchrones.
*   **Configuration**: Via variables d'environnement (`.env`).
*   **Tâches**: Définies dans `api/main.py` (ex: `run_scan_tool`). Les workers écoutent Redis et exécutent ces tâches.

### 2.6 Agent Client (Python/WebSocket)

*   **Fichier principal**: `client/client_agent.py`.
*   **Dépendances clés**: `websockets`, `requests` (pour enregistrement initial).
*   **Fonctionnalités**:
    *   Enregistrement initial via API REST (`/api/clients/register`).
    *   Connexion persistante à l'API via WebSocket (`/ws/{client_uuid}`).
    *   Gestion mTLS (à configurer avec des certificats).
    *   Envoi de heartbeats.
    *   Réception de commandes (`type: command`).
    *   Exécution de commandes système via `subprocess`.
    *   Envoi des résultats (`type: command_result`).
*   **Packaging**: Peut être packagé en exécutable avec PyInstaller (`dist/cybershield_agent`).

### 2.7 Scanner Gratuit

*   **Technologie**: Scripts natifs (ex: `client/scanners/windows_scan_free.ps1`).
*   **Fonctionnement**: Entièrement local, pas de communication backend.

### 2.8 Outils de Scan (Dockerisés)

*   **Gestion**: Définis comme services potentiels dans `docker-compose.yml` (non inclus par défaut, à ajouter selon les besoins).
*   **Exécution**: Lancés par les workers Celery (via Docker SDK ou `subprocess`).

## 3. Sécurité

*   **Communication**: HTTPS pour le frontend/API REST, WSS pour WebSocket. mTLS fortement recommandé pour l'authentification de l'agent.
*   **Authentification Agent**: Basée sur l'UUID client via l'URL WebSocket, renforcée par mTLS.
*   **Secrets**: Gérés via variables d'environnement (`.env` file).
*   **Isolation**: Conteneurisation Docker.

## 4. Flux de Données (Scan Pro/Entreprise)

1.  L'Agent Client collecte les infos système et s'enregistre via `POST /api/clients/register`, obtenant/confirmant son `client_uuid`.
2.  L'Agent établit une connexion WebSocket vers `/ws/{client_uuid}` (idéalement avec mTLS).
3.  L'API (ou un utilisateur via une interface non implémentée) initie un scan via `POST /api/scans` pour ce `client_uuid`.
4.  L'API crée une entrée `Scan` et une `ScanTask` initiale (ex: Nmap) dans la DB.
5.  L'API envoie la tâche au worker Celery via Redis.
6.  Le Worker Celery exécute la tâche (ex: lance un conteneur Nmap).
7.  Une fois la tâche Celery terminée, elle met à jour le statut de la `ScanTask` (via API ou directement si configuré).
8.  L'API, basée sur la logique de scan, peut envoyer une nouvelle commande à l'Agent via WebSocket (`type: command`).
9.  L'Agent reçoit la commande, l'exécute localement.
10. L'Agent renvoie le résultat via WebSocket (`type: command_result`).
11. L'API reçoit le résultat, met à jour la `ScanTask` correspondante dans la DB.
12. Le processus se répète jusqu'à la fin du scan.
13. Une tâche de génération de rapport est lancée (via Celery).
14. Le rapport est généré et stocké.
15. L'API notifie l'agent (ou l'utilisateur) de la disponibilité du rapport.

## 5. Déploiement

*   Utilise `docker-compose.yml` pour orchestrer tous les services backend.
*   Nécessite Docker et Docker Compose sur le serveur hôte.
*   La configuration se fait via le fichier `.env`.
*   Voir `guide_installation.md` pour les étapes détaillées.

## 6. Extensibilité

*   **Nouveaux outils**: Ajouter un service Docker, créer une tâche Celery, intégrer dans la logique de scan de l'API.
*   **Frontend**: Peut être remplacé par un framework moderne (React, Vue) si nécessaire.
*   **Espace Client**: Peut être ajouté avec une authentification JWT et des endpoints API REST dédiés.

## 7. Tests

*   Les tests unitaires existants (`tests/`) peuvent nécessiter une mise à jour pour refléter la nouvelle architecture (BDD, WebSocket).
*   Les tests d'intégration nécessitent un environnement Docker fonctionnel.

## 8. Journalisation

*   **API**: `pentesting_api.log` dans le conteneur API.
*   **Agent**: `pentesting_agent.log` sur la machine client.
*   **Docker**: Via `docker compose logs <service_name>`.

