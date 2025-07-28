# Fichier: api/dependencies.py

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# Utiliser une base de données SQLite asynchrone pour la simplicité
# Assurez-vous que le chemin est correct et accessible
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////home/ubuntu/cybershield/cybershield_plateforme_complete/api/cybershield_async.db")

engine = create_async_engine(DATABASE_URL, echo=False) # Mettre echo=True pour le débogage SQL
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    """Dependency pour obtenir une session de base de données asynchrone."""
    async with AsyncSessionLocal() as session:
        yield session

# Importer les modèles pour référence si nécessaire (par exemple, pour get_current_user)
# from .models import User 

