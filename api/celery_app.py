# Fichier: api/celery_app.py

from celery import Celery
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis un fichier .env (si présent)
load_dotenv()

# Utiliser les variables d'environnement pour la configuration
# Fournir des valeurs par défaut pour le développement local si non définies
# En production, ces variables devraient être définies dans l'environnement
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Créer l'instance Celery
# Le premier argument est le nom du module courant, utile pour l'auto-découverte des tâches.
# Le deuxième argument 'broker' spécifie l'URL du message broker (Redis ici).
# Le troisième argument 'backend' spécifie l'URL du backend de résultats (Redis ici).
# L'argument 'include' liste les modules où Celery doit chercher les tâches.

celery_app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')
# ou une configuration similaire

celery = Celery(
    "cybershield_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["tasks"] # Chemin vers le module contenant les définitions de tâches
)

# Configuration optionnelle de Celery (peut être chargée depuis un fichier de config Flask aussi)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Optionnel: Limiter le nombre de tâches pré-chargées par worker pour économiser mémoire
    # worker_prefetch_multiplier=1,
    # Optionnel: Définir une file d'attente par défaut
    # task_default_queue='default',
)

# Optionnel: Configuration pour la découverte automatique des tâches
# celery_app.autodiscover_tasks() # Découvre les tâches dans les modules listés dans 'include'

if __name__ == "__main__":
    # Ceci permet de lancer le worker Celery directement pour le test
    # Exemple de commande: celery -A api.celery_app worker --loglevel=info
    celery.start()

