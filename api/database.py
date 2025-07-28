from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Récupération de l'URL de la base de données depuis les variables d'environnement
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/cybershield")

# Création du moteur SQLAlchemy
engine = create_engine(DATABASE_URL)

# Création d'une classe SessionLocal pour les sessions de base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Création d'une classe Base pour les modèles déclaratifs
Base = declarative_base()

# Fonction de dépendance pour obtenir une session de base de données
def get_db():
    """
    Fonction de dépendance pour obtenir une session de base de données.
    Cette fonction est utilisée avec FastAPI pour injecter une session de base de données
    dans les routes qui en ont besoin.
    
    Yields:
        Session: Une session SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def create_db_and_tables():
    Base.metadata.create_all(engine)
