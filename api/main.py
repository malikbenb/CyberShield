from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette_prometheus import PrometheusMiddleware, metrics
import time
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge
from sqlalchemy.orm import Session

# Import des nouveaux routers FastAPI
from auth_fastapi import auth_router
from dashboard_routes_fastapi import dashboard_router
from admin_routes_fastapi import admin_router
from payment_routes import payment_router  # Ce fichier utilise déjà APIRouter
from auth_check_routes import auth_check_router  # Nouveau router pour la vérification des abonnements
from stats_routes import stats_router  # Nouveau router pour les statistiques
from database import get_db, engine, Base, create_db_and_tables # Ajout de create_db_and_tables
from models_fastapi import User, ScanHistory, Report, Subscription, SubscriptionPlan # Import direct des modèles pour s'assurer qu'ils sont enregistrés avec Base.metadata


# Création des métriques Prometheus
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total', 
    'Total des requêtes HTTP', 
    ['method', 'endpoint', 'status']
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds', 
    'Durée des requêtes HTTP',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'active_users',    
    'Nombre d\'utilisateurs actifs'
)

SCAN_TOTAL = Counter(
    'scan_total',
    'Nombre total de scans effectués',
    ['type', 'status']
)

SCAN_IN_PROGRESS = Gauge(
    'scan_in_progress',
    'Nombre de scans en cours'
)

SCAN_FAILED_TOTAL = Counter(
    'scan_failed_total',
    'Nombre total de scans échoués'
)

SCAN_DURATION = Histogram(
    'scan_duration_seconds',
    'Durée des scans',
    ['type']
)

# Middleware pour mesurer la durée des requêtes
class PrometheusMiddlewareCustom(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method, 
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response


# Création de l'application FastAPI
app = FastAPI(
    title="CyberShield API",
    description="API pour la plateforme de pentesting CyberShield",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ajout du middleware Prometheus personnalisé
app.add_middleware(PrometheusMiddlewareCustom)

# Ajout des routers FastAPI
app.include_router(auth_router, tags=["authentication"])
app.include_router(dashboard_router, tags=["dashboard"])
app.include_router(admin_router, tags=["admin"])
app.include_router(payment_router, tags=["payment"])
app.include_router(auth_check_router, tags=["auth_check"])  # Nouveau router pour la vérification des abonnements
app.include_router(stats_router, tags=["statistics"])  # Nouveau router pour les statistiques

# Exposition des métriques Prometheus
app.add_route("/metrics", metrics)

@app.get("/", tags=["root"])
async def root():
    return {"message": "Bienvenue sur l'API CyberShield"}

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

# Création des tables dans la base de données
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Point d'entrée pour Gunicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
