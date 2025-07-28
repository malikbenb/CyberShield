# Guide d'installation et d'utilisation (Mis à Jour)

Ce document fournit des instructions détaillées pour installer, configurer et utiliser la plateforme de pentest éthique automatisé refactorisée.

## 1. Installation

### 1.1 Prérequis

Avant d'installer le système, assurez-vous que votre environnement serveur répond aux exigences suivantes :

*   **Serveur Hôte**:
    *   Système d'exploitation : Linux (recommandé)
    *   Docker: Version récente installée.
    *   Docker Compose: Plugin V2 (commande `docker compose`) installé.
    *   Accès Internet (pour télécharger les images Docker).
    *   Ressources suffisantes (CPU, RAM, Disque) pour exécuter les conteneurs, notamment les outils de scan.
*   **Machine Client (pour l'Agent Pro/Entreprise)**:
    *   Système d'exploitation : Windows, macOS, ou Linux avec privilèges administrateur/root.
    *   Accès réseau au serveur hébergeant l'API.

### 1.2 Installation du Serveur (Backend)

1.  **Cloner le Dépôt du Projet**
    Sur le serveur qui hébergera la plateforme, clonez le dépôt contenant le code source.
    ```bash
    # Remplacez par l'URL réelle du dépôt si disponible
    # git clone https://github.com/votre-utilisateur/pentesting-project.git
    # cd pentesting-project
    
    # Si vous avez reçu les fichiers autrement, assurez-vous que la structure est correcte:
    # pentesting_project/
    # |- api/
    # |- client/
    # |- docker/
    # |- docs/
    # |- frontend/ (ou Test Incubateur/CyberShield-Local-V8/client/)
    # |- tests/
    # |- .env
    # |- docker-compose.yml
    # |- nginx.conf
    # |- ... autres fichiers
    cd /chemin/vers/votre/projet/pentesting_platform
    ```

2.  **Configurer l'Environnement**
    Créez ou modifiez le fichier `.env` à la racine du projet pour définir les variables d'environnement. Assurez-vous de définir des mots de passe robustes et de changer la `JWT_SECRET_KEY`.
    ```ini
    # PostgreSQL Configuration
    POSTGRES_USER=pentest_user
    POSTGRES_PASSWORD=changer_ce_mot_de_passe_secret
    POSTGRES_DB=pentest_db
    POSTGRES_HOST=db
    POSTGRES_PORT=5432
    DATABASE_URL=postgresql+asyncpg://pentest_user:changer_ce_mot_de_passe_secret@db:5432/pentest_db
    
    # Redis Configuration
    REDIS_HOST=redis
    REDIS_PORT=6379
    CELERY_BROKER_URL=redis://redis:6379/0
    CELERY_RESULT_BACKEND=redis://redis:6379/0
    
    # JWT Configuration
    JWT_SECRET_KEY=changer_cette_cle_secrete_jwt_tres_longue
    
    # API Configuration (généralement pas besoin de changer)
    API_HOST=0.0.0.0
    API_PORT=8000
    ```

3.  **Préparer le Frontend**
    Assurez-vous que les fichiers du frontend (HTML, CSS, JS, images, scanners gratuits) se trouvent dans un répertoire accessible, par exemple `frontend/`. Le `docker-compose.yml` et `nginx.conf` actuels supposent que le frontend est dans `./frontend`. Si vos fichiers sont dans `Test Incubateur/CyberShield-Local-V8/client`, copiez ou déplacez-les :
    ```bash
    # Si nécessaire, copiez les fichiers frontend
    mkdir frontend
    cp -r "Test Incubateur/CyberShield-Local-V8/client/." frontend/
    ```
    *Note: Les chemins des scanners gratuits dans `frontend/js/download.js` pointent vers `/client/scanners/...`. Assurez-vous que ces fichiers sont présents dans `frontend/scanners/`.* Ajustez `download.js` si nécessaire pour pointer vers les bons chemins relatifs servis par Nginx (ex: `/scanners/windows/WindowsFreeScan.exe`).

4.  **Démarrer les Services Docker**
    Utilisez Docker Compose pour construire les images (si nécessaire) et démarrer tous les conteneurs en arrière-plan.
    ```bash
    docker compose up -d --build
    ```
    * `--build`: Force la reconstruction des images (utile après des modifications du code ou du Dockerfile).
    * `-d`: Lance les conteneurs en mode détaché (arrière-plan).

5.  **Vérifier le Statut des Services**
    ```bash
    docker compose ps
    ```
    Tous les services (nginx, api, db, redis, worker) devraient être listés avec le statut `running` ou `healthy`.

6.  **Vérifier l'Accès à l'Interface Web**
    Ouvrez un navigateur et accédez à l'adresse IP ou au nom de domaine de votre serveur (ex: `http://votre_serveur_ip`). Vous devriez voir l'interface de CyberShield Algeria.

### 1.3 Installation de l'Agent Client (Pro/Entreprise)

L'agent client doit être installé sur chaque machine cible que vous souhaitez tester avec les offres Pro ou Entreprise.

1.  **Obtenir l'Agent**
    *   **Option 1: Utiliser l'exécutable pré-packagé**
        Si un exécutable a été fourni (ex: `dist/cybershield_agent` pour Linux, ou des versions pour Windows/macOS), copiez-le sur la machine cible.
    *   **Option 2: Packager l'Agent manuellement**
        Si vous avez le code source (`client/client_agent.py`) et les dépendances (`websockets`, `requests`), vous pouvez le packager sur une machine compatible :
        ```bash
        # Installer PyInstaller
        pip install pyinstaller websockets requests
        
        # Packager (adapter pour Windows/macOS si nécessaire)
        pyinstaller --onefile --name cybershield_agent client/client_agent.py
        
        # L'exécutable se trouvera dans le dossier dist/
        ```

2.  **Configurer et Exécuter l'Agent**
    Ouvrez un terminal **avec des privilèges administrateur/root** sur la machine cible et lancez l'agent en spécifiant les URLs de l'API.
    *   Remplacez `http://votre_serveur_ip` et `ws://votre_serveur_ip` par l'adresse IP ou le nom de domaine correct de votre serveur.
    *   Si vous avez configuré HTTPS et WSS (recommandé), utilisez `https://...` et `wss://...`.

    ```bash
    # Sur Linux/macOS
    sudo ./cybershield_agent --api-rest-url http://votre_serveur_ip/api --api-ws-url ws://votre_serveur_ip/ws
    
    # Sur Windows (dans un terminal administrateur)
    .\cybershield_agent.exe --api-rest-url http://votre_serveur_ip/api --api-ws-url ws://votre_serveur_ip/ws
    ```
    L'agent va :
    *   Collecter les informations système.
    *   Contacter l'API REST pour s'enregistrer (ou confirmer son UUID).
    *   Établir une connexion WebSocket persistante avec l'API.
    *   Attendre les commandes de l'API.

## 2. Utilisation

### 2.1 Scanner Gratuit

1.  Accédez à l'interface web de la plateforme (`http://votre_serveur_ip`).
2.  Allez à la section "Scanners".
3.  Cliquez sur le bouton "Version Gratuite" pour votre système d'exploitation.
4.  Acceptez le consentement.
5.  Le script/exécutable du scanner gratuit sera téléchargé.
6.  Exécutez le fichier téléchargé sur votre machine locale.
7.  Le scan s'effectuera localement et un rapport HTML sera généré et ouvert automatiquement.

### 2.2 Scan Pro/Entreprise (via Agent)

1.  Assurez-vous que l'Agent Client est installé et **en cours d'exécution avec des privilèges élevés** sur la machine cible (voir section 1.3).
2.  **Initiation du Scan**: L'initiation du scan se fait actuellement via un appel API direct (une interface utilisateur pour cela pourrait être ajoutée au frontend).
    *   Vous aurez besoin du `client_uuid` de l'agent (affiché dans les logs de l'agent au démarrage ou récupérable via une future API).
    *   Exemple d'appel API pour démarrer un scan Pro sur une cible :
        ```bash
        curl -X POST "http://votre_serveur_ip/api/scans?client_uuid=UUID_DE_VOTRE_AGENT" \
             -H "Content-Type: application/json" \
             -d '{
                   "targets": ["192.168.1.10"], 
                   "scan_type": "pro"
                 }'
        ```
3.  **Surveillance**: L'API enverra des commandes à l'agent via WebSocket. Vous pouvez surveiller les logs de l'agent (`pentesting_agent.log`) et de l'API (`docker compose logs api`, `docker compose logs worker`) pour voir la progression.
4.  **Résultats**: L'agent exécute les commandes et renvoie les résultats à l'API via WebSocket.
5.  **Rapport**: Une fois le scan terminé, un rapport sera généré côté serveur (dans le volume `reports/`). L'accès/téléchargement du rapport nécessiterait un endpoint API supplémentaire ou une fonctionnalité dans l'espace client (non implémenté actuellement).

## 3. Dépannage

*   **Problèmes de Connexion Agent**: Vérifiez les URLs de l'API dans la commande de l'agent. Assurez-vous que le serveur est accessible depuis la machine client (pare-feu, réseau). Vérifiez les logs Nginx (`docker compose logs nginx`) et API (`docker compose logs api`).
*   **Services Docker non démarrés**: Utilisez `docker compose ps` pour voir le statut. Utilisez `docker compose logs <service_name>` (ex: `api`, `db`, `worker`) pour voir les erreurs spécifiques.
*   **Erreurs de Base de Données**: Vérifiez les logs du conteneur `db` (`docker compose logs db`). Assurez-vous que les identifiants dans `.env` sont corrects.
*   **Tâches Celery échouent**: Vérifiez les logs du `worker` (`docker compose logs worker`). Assurez-vous que Redis est accessible (`docker compose logs redis`).
*   **Agent non exécuté avec privilèges**: Certaines commandes échoueront. Relancez l'agent avec `sudo` (Linux/macOS) ou en tant qu'administrateur (Windows).

## 4. Maintenance

*   **Mise à jour**: Arrêtez les services (`docker compose down`), mettez à jour le code source (ex: `git pull`), puis redémarrez (`docker compose up -d --build`).
*   **Sauvegarde**: Sauvegardez régulièrement le volume PostgreSQL (`postgres_data` défini dans `docker-compose.yml`) et les répertoires `reports/` et `results/` (qui sont actuellement dans le conteneur API, idéalement, ils devraient être des volumes mappés sur l'hôte).
*   **Logs**: Gérez la rotation des logs Docker ou configurez une solution de journalisation centralisée.

## 5. Sécurité Avancée (mTLS)

Pour une sécurité accrue, configurez mTLS pour la connexion WebSocket Agent <-> API :

1.  **Générez les certificats**: Une autorité de certification (CA), un certificat serveur pour Nginx, et des certificats clients uniques pour chaque agent.
2.  **Configurez Nginx**: Décommentez et adaptez la section `location /ws` dans `nginx.conf` pour activer `ssl_verify_client` et spécifier le CA client.
3.  **Configurez l'Agent**: Modifiez `client_agent.py` pour utiliser le contexte SSL avec les certificats client (`_get_ssl_context` function) et utilisez l'URL `wss://`.
4.  **Configurez l'API (Optionnel)**: L'API peut vérifier les informations du certificat client passées par Nginx via les en-têtes (`X-Client-Verify`, `X-Client-DN`).

