# Fichier: api/Dockerfile

# Utiliser une image Python officielle comme image de base
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier des dépendances
# Copier requirements.txt d'abord pour profiter du cache Docker
COPY requirements.txt requirements.txt

# Installer les dépendances
# --no-cache-dir réduit la taille de l'image
# --upgrade pip s'assure qu'on a la dernière version
# Ajout de uvicorn car il est nécessaire pour exécuter FastAPI avec Gunicorn
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn

# Copier le reste du code de l'application API dans le répertoire de travail
COPY . .

# Exposer le port sur lequel l'application FastAPI écoutera via Gunicorn/Uvicorn
# Le port exposé ici est interne au conteneur. Nginx le mappera.
EXPOSE 8000

# Commande corrigée pour lancer l'application FastAPI avec Gunicorn et Uvicorn workers
# Utilisation de '-k uvicorn.workers.UvicornWorker' pour spécifier le worker ASGI
# Le bind est sur 0.0.0.0:8000 pour correspondre au port exposé et au mapping docker-compose
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--workers", "1", "--timeout", "120", "--bind", "0.0.0.0:8000", "main:app"]

# Note: Pour lancer le worker Celery, vous utiliserez une commande différente
# dans docker-compose.yml, en utilisant la même image mais en surchargeant le CMD.
# Exemple: command: celery -A api.celery_app worker --loglevel=info

