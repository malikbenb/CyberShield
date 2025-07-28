from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import jwt
import os

from models_fastapi import User
from database import get_db

# Configuration JWT
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

# Router pour l\'authentification
auth_check_router = APIRouter(prefix="/auth", tags=["auth"])

# Schéma de sécurité pour les tokens Bearer
security = HTTPBearer()

@auth_check_router.get("/check_subscription")
async def check_subscription(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Endpoint pour vérifier l\'abonnement d\'un utilisateur.
    Utilisé par nginx auth_request pour sécuriser les téléchargements.
    """
    try:
        # Récupérer l\'URI originale depuis nginx
        original_uri = request.headers.get("X-Original-URI", "")
        
        # Déterminer le type de scanner requis
        required_subscription = None
        if "/scanners/pro/" in original_uri:
            required_subscription = "pro"
        elif "/scanners/enterprise/" in original_uri:
            required_subscription = "enterprise"
        else:
            # Scanner gratuit, pas de vérification nécessaire
            return {"status": "ok", "message": "Scanner gratuit autorisé"}
        
        # Vérifier la présence du token
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token d\'authentification requis"
            )
        
        # Décoder le token JWT
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalide"
                )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide ou expiré"
            )
        
        # Récupérer l\'utilisateur
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        
        # Vérifier l\'abonnement actif
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Abonnement inactif"
            )
        
        # Vérifier le type d\'abonnement
        if required_subscription == "pro" and user.offer_type not in ["pro", "enterprise"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Abonnement Pro ou Entreprise requis"
            )
        elif required_subscription == "enterprise" and user.offer_type != "enterprise":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Abonnement Entreprise requis"
            )
        
        return {
            "status": "ok",
            "message": f"Accès autorisé pour {required_subscription}",
            "user_id": user.id,
            "subscription_type": user.offer_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la vérification de l'abonnement"
        )
