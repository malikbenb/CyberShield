# Fichier : api/models.py

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os 

db = SQLAlchemy()

# --- Constantes pour les Offres et Quotas ---
OFFER_TYPES = ["free", "pro", "enterprise"]
QUOTAS = {
    "free": 0, 
    "pro": 10, 
    "enterprise": 20 
}
DEFAULT_OFFER = "pro"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # --- Champs pour la gestion des offres et quotas ---
    offer_type = db.Column(db.String(50), nullable=False, default=DEFAULT_OFFER)
    scan_quota_limit = db.Column(db.Integer, nullable=False, default=QUOTAS[DEFAULT_OFFER])
    scan_quota_used = db.Column(db.Integer, nullable=False, default=0)
    quota_period_start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # --- Champs pour la gestion des abonnements (Manuel) ---
    subscription_start_date = db.Column(db.DateTime, nullable=True)
    subscription_end_date = db.Column(db.DateTime, nullable=True)
    
    # --- Champ pour le rôle Admin ---
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    # Relation avec l\historique des scans
    scans = db.relationship("ScanHistory", backref="user", lazy=True)

    # Flask-Login integration
    @property
    def is_active(self):
        """Vérifie si l'utilisateur est actif (abonnement valide pour les offres payantes)."""
        if self.offer_type == "free":
            return True
        return self.subscription_end_date is not None and self.subscription_end_date > datetime.utcnow()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    # --- Méthodes pour la gestion des quotas ---
    def update_quota_limit(self):
        self.scan_quota_limit = QUOTAS.get(self.offer_type, 0)

    def reset_quota_if_needed(self):
        now = datetime.utcnow()
        period_end = self.quota_period_start + timedelta(days=30) 
        if now >= period_end:
            self.quota_period_start = now
            self.scan_quota_used = 0
            print(f"Quota réinitialisé pour l'utilisateur {self.id}")
            return True
        return False

    def has_quota_remaining(self, requested_scans=1):
        if not self.is_active:
             return False
        self.reset_quota_if_needed() 
        return (self.scan_quota_used + requested_scans) <= self.scan_quota_limit
        
    def increment_quota_used(self, count=1):
        if self.has_quota_remaining(requested_scans=count):
            self.scan_quota_used += count
            return True
        return False

    def __repr__(self):
        role = "Admin" if self.is_admin else "User"
        return f"<{role} {self.email} ({self.offer_type})>"

class ScanHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    batch_id = db.Column(db.String(50), nullable=True, index=True) 
    scan_type = db.Column(db.String(20), nullable=False, default="pro") # pro, enterprise
    target_ip = db.Column(db.String(100), nullable=False) 
    scan_start_time = db.Column(db.DateTime, default=datetime.utcnow)
    scan_end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="queued")
    vulnerability_score = db.Column(db.Float, nullable=True) 
    celery_task_id = db.Column(db.String(100), nullable=True)
    
    report = db.relationship("Report", backref="scan", uselist=False, lazy=True)

    def __repr__(self):
        return f"<ScanHistory {self.id} for User {self.user_id} Target {self.target_ip}>"

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scan_history.id"), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    format = db.Column(db.String(20), default="json") 

    def __repr__(self):
        return f"<Report {self.id} for Scan {self.scan_id}>"

def init_db(app):
    db.init_app(app)
    with app.app_context():
        print("Création/Vérification des tables de base de données...")
        db.create_all() 
        print("Tables de base de données vérifiées/créées.")

