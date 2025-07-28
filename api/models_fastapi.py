# Fichier : api/models_fastapi.py
# Version SQLAlchemy standard pour FastAPI

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func # Pour default=func.now()
from datetime import datetime, timedelta
import os


# --- Constantes pour les Offres et Quotas (gardées pour référence) ---
OFFER_TYPES = ["free", "pro", "enterprise"]
QUOTAS = {
    "free": 0, 
    "pro": 10, 
    "enterprise": 20 
}
DEFAULT_OFFER = "pro"

class User(Base):
    __tablename__ = "user" # Nom de la table

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False) # Renommé depuis password_hash
    created_at = Column(DateTime, default=func.now()) # Utiliser func.now() pour default DB
    
    # --- Champs pour la gestion des offres et quotas ---
    offer_type = Column(String(50), nullable=False, default=DEFAULT_OFFER)
    scan_quota_limit = Column(Integer, nullable=False, default=QUOTAS[DEFAULT_OFFER])
    scan_quota_used = Column(Integer, nullable=False, default=0)
    quota_period_start = Column(DateTime, nullable=False, default=func.now())
    
    # --- Champs pour la gestion des abonnements (Manuel) ---
    subscription_start_date = Column(DateTime, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)
    
    # --- Champ pour le rôle Admin ---
    is_admin = Column(Boolean, nullable=False, default=False)

    # Relation avec l'historique des scans
    scans = relationship("ScanHistory", back_populates="user") # Utiliser back_populates
    # Relation avec les abonnements (si Subscription model existe)
    subscriptions = relationship("Subscription", back_populates="user")

    # Propriété pour vérifier si l'utilisateur est actif (logique métier)
    @property
    def is_active(self):
        """Vérifie si l'utilisateur est actif (abonnement valide pour les offres payantes)."""
        if self.offer_type == "free":
            return True
        # Utiliser datetime.utcnow() pour comparer avec le temps actuel
        return self.subscription_end_date is not None and self.subscription_end_date > datetime.utcnow()

    # --- Méthodes pour la gestion des quotas (gardées comme logique métier) ---
    def update_quota_limit(self):
        self.scan_quota_limit = QUOTAS.get(self.offer_type, 0)

    def reset_quota_if_needed(self):
        now = datetime.utcnow()
        # Assurez-vous que quota_period_start est bien un datetime
        if isinstance(self.quota_period_start, datetime):
            period_end = self.quota_period_start + timedelta(days=30) 
            if now >= period_end:
                self.quota_period_start = now
                self.scan_quota_used = 0
                # Utilisation de double antislash pour échapper
                print(f"Quota réinitialisé pour l\'utilisateur {self.id}")
                return True
        else:
             # Gérer le cas où quota_period_start n'est pas initialisé (ne devrait pas arriver)
             self.quota_period_start = now
             self.scan_quota_used = 0
             # Utilisation de double antislash pour échapper
             print(f"Quota initialisé/réinitialisé (date manquante) pour l\'utilisateur {self.id}")
             return True
        return False

    def has_quota_remaining(self, requested_scans=1):
        if not self.is_active:
             return False
        self.reset_quota_if_needed() 
        return (self.scan_quota_used + requested_scans) <= self.scan_quota_limit
        
    def increment_quota_used(self, count=1):
        # Note: La logique de vérification est déjà dans has_quota_remaining
        # Cette méthode devrait juste incrémenter si possible
        # La vérification devrait être faite avant d'appeler cette méthode
        # if self.has_quota_remaining(requested_scans=count):
        self.scan_quota_used += count
        # return True
        # return False

    def __repr__(self):
        role = "Admin" if self.is_admin else "User"
        return f"<{role} {self.email} ({self.offer_type})>"

class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    batch_id = Column(String(50), nullable=True, index=True) 
    scan_type = Column(String(20), nullable=False, default="pro") # pro, enterprise
    target_ip = Column(String(100), nullable=False) 
    scan_start_time = Column(DateTime, default=func.now())
    scan_end_time = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="queued")
    vulnerability_score = Column(Float, nullable=True) 
    celery_task_id = Column(String(100), nullable=True)
    
    user = relationship("User", back_populates="scans")
    report = relationship("Report", back_populates="scan", uselist=False)

    def __repr__(self):
        return f"<ScanHistory {self.id} for User {self.user_id} Target {self.target_ip}>"

class Report(Base):
    __tablename__ = "report"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scan_history.id"), nullable=False)
    generated_at = Column(DateTime, default=func.now())
    content = Column(Text, nullable=False)
    format = Column(String(20), default="json") 

    scan = relationship("ScanHistory", back_populates="report")

    def __repr__(self):
        return f"<Report {self.id} for Scan {self.scan_id}>"

# --- Modèle Subscription (ajouté basé sur admin_routes) ---
class Subscription(Base):
    plan_id = Column(Integer, ForeignKey("subscription_plan.id"), nullable=False) # Assurez-vous que chaque abonnement a un plan
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")

    __tablename__ = "subscription"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    subscription_type = Column(String(50), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="active") # ex: active, cancelled, expired
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription {self.id} for User {self.user_id} ({self.subscription_type})>"


# --- Modèle SubscriptionPlan --- 
class SubscriptionPlan(Base):
    __tablename__ = "subscription_plan"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) # ex: "Pro", "Enterprise"
    price_monthly = Column(Float, nullable=True) # Prix par mois
    price_annually = Column(Float, nullable=True) # Prix par an
    scan_quota = Column(Integer, nullable=False) # Quota de scans inclus
    description = Column(Text, nullable=True) # Description du plan
    is_active = Column(Boolean, default=True) # Pour activer/désactiver un plan
    created_at = Column(DateTime, default=func.now())

    # Relation inverse avec les abonnements
    subscriptions = relationship("Subscription", back_populates="plan")

    def __repr__(self):
        return f"<SubscriptionPlan {self.name} (Quota: {self.scan_quota})>"


# Note: La création des tables se fera via Alembic ou une initialisation séparée,
# pas via une fonction init_db(app) comme avec Flask-SQLAlchemy.



