# Fichier : api/admin_routes_fastapi.py
# Version FastAPI

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

# Importer les modèles SQLAlchemy, la session DB, et l'authentification
from models_fastapi import User, ScanHistory, Report, Subscription, QUOTAS # Utiliser models_fastapi
from database import get_db
from auth_fastapi import get_current_user # Utilise l'authentification JWT

# --- Dépendance pour vérifier si l'utilisateur est admin ---
async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs"
        )
    return current_user

# --- Modèles Pydantic pour l'administration ---

class UserAdminBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    offer_type: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    scan_quota_limit: Optional[int] = None
    scan_quota_used: Optional[int] = None

class UserAdminResponse(UserAdminBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ScanHistoryAdminItem(BaseModel):
    id: int
    target_ip: str
    scan_type: str
    status: str
    created_at: datetime # Utiliser created_at si disponible, sinon scan_start_time
    completed_at: Optional[datetime] = None
    score: Optional[float] = None

    class Config:
        orm_mode = True

class UserAdminDetailResponse(UserAdminResponse):
    scan_history: List[ScanHistoryAdminItem] = []

class UserAdminUpdate(BaseModel):
    # Permet de mettre à jour seulement certains champs
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    offer_type: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    scan_quota_limit: Optional[int] = None
    scan_quota_used: Optional[int] = None

class SubscriptionAdminBase(BaseModel):
    user_id: int
    subscription_type: str
    start_date: datetime
    end_date: datetime
    price: float
    status: str = "active"
    notes: Optional[str] = None

class SubscriptionAdminCreate(SubscriptionAdminBase):
    pass

class SubscriptionAdminResponse(SubscriptionAdminBase):
    id: int
    created_at: datetime
    user_name: Optional[str] = None # Ajouté pour l'affichage
    user_email: Optional[EmailStr] = None # Ajouté pour l'affichage

    class Config:
        orm_mode = True

class SubscriptionAdminUpdate(BaseModel):
    subscription_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    price: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ScanAdminBase(BaseModel):
    id: int
    user_id: int
    target_ip: str
    scan_type: str
    status: str
    score: Optional[float] = None
    created_at: datetime # Utiliser created_at si disponible
    completed_at: Optional[datetime] = None
    user_name: Optional[str] = None
    user_email: Optional[EmailStr] = None

class ScanAdminResponse(ScanAdminBase):
    class Config:
        orm_mode = True

class ReportAdminData(BaseModel):
    id: int
    content: Dict[str, Any] # Supposant que le contenu est JSON
    created_at: datetime

    class Config:
        orm_mode = True

class ScanAdminDetailResponse(ScanAdminBase):
    report: Optional[ReportAdminData] = None

class MonthlySubscriptionStat(BaseModel):
    month: int
    pro: int
    enterprise: int

class RecentActivityItem(BaseModel):
    type: str
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    scan_id: Optional[int] = None
    target_ip: Optional[str] = None
    subscription_id: Optional[int] = None
    subscription_type: Optional[str] = None
    timestamp: datetime

class DashboardStatsResponse(BaseModel):
    total_users: int
    active_subscriptions: int
    total_scans: int
    estimated_revenue: float
    offer_distribution: Dict[str, int]
    monthly_subscriptions: List[MonthlySubscriptionStat]
    recent_activity: List[RecentActivityItem]

# --- Router FastAPI pour l'Admin ---
admin_router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
    dependencies=[Depends(get_current_admin_user)], # Toutes les routes ici nécessitent un admin
    responses={403: {"description": "Accès non autorisé"}},
)

# --- Conversion des Routes Admin ---

@admin_router.get("/users", response_model=List[UserAdminResponse])
async def get_users_admin(db: Session = Depends(get_db)):
    """Récupère la liste des utilisateurs pour l'administration."""
    users = db.query(User).all()
    return users

@admin_router.get("/users/{user_id}", response_model=UserAdminDetailResponse)
async def get_user_admin(user_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """Récupère les détails d'un utilisateur spécifique et son historique de scans."""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    
    # Récupérer l'historique des scans
    # Assurez-vous que ScanHistory a bien un champ `created_at` ou adaptez le tri
    scans_db = db.query(ScanHistory).filter(ScanHistory.user_id == user_id).order_by(desc(ScanHistory.scan_start_time)).all()
    
    # Convertir les scans pour la réponse
    scan_history_response = [ScanHistoryAdminItem.from_orm(scan) for scan in scans_db]
    
    # Créer la réponse détaillée
    user_response = UserAdminDetailResponse.from_orm(user)
    user_response.scan_history = scan_history_response
    
    return user_response

@admin_router.put("/users/{user_id}", response_model=UserAdminResponse)
async def update_user_admin(user_id: int = Path(..., ge=1), user_update: UserAdminUpdate = Body(...), db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Met à jour les informations d'un utilisateur par un admin."""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    update_data = user_update.dict(exclude_unset=True)
    updated = False

    for key, value in update_data.items():
        if hasattr(user, key) and value is not None:
            # Vérification spéciale pour is_admin
            if key == "is_admin" and not value and user.is_admin:
                admin_count = db.query(User).filter(User.is_admin == True).count()
                if admin_count <= 1:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossible de retirer les droits au dernier administrateur")
            setattr(user, key, value)
            updated = True
    
    if updated:
        try:
            db.commit()
            db.refresh(user)
            print(f"Admin {current_admin.email} a mis à jour l'utilisateur {user.email}")
            return user
        except Exception as e:
            db.rollback()
            print(f"Erreur DB PUT /admin/users/{user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur serveur: {str(e)}")
    else:
        # Si aucune donnée fournie pour la mise à jour, retourner l'utilisateur actuel
        return user

@admin_router.post("/users/{user_id}/reset-password") # Pas de response_model car action simulée
async def reset_user_password_admin(user_id: int = Path(..., ge=1), db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """(Simulé) Demande la réinitialisation du mot de passe d'un utilisateur."""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    
    # Logique d'envoi d'email à implémenter ici
    print(f"Admin {current_admin.email} a demandé la réinitialisation du mot de passe pour {user.email}")
    return {"message": "Demande de réinitialisation de mot de passe envoyée (simulation)"}

@admin_router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user_admin(user_id: int = Path(..., ge=1), db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Supprime un utilisateur."""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    if user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossible de supprimer le dernier administrateur")
    
    try:
        # Gérer les dépendances (ex: scans, abonnements) avant suppression si nécessaire
        # db.query(ScanHistory).filter(ScanHistory.user_id == user_id).delete()
        # db.query(Subscription).filter(Subscription.user_id == user_id).delete()
        
        db.delete(user)
        db.commit()
        print(f"Admin {current_admin.email} a supprimé l'utilisateur {user.email}")
        return {"message": "Utilisateur supprimé avec succès"}
    except Exception as e:
        db.rollback()
        print(f"Erreur DB DELETE /admin/users/{user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur serveur: {str(e)}")

@admin_router.get("/subscriptions", response_model=List[SubscriptionAdminResponse])
async def get_subscriptions_admin(db: Session = Depends(get_db)):
    """Récupère la liste des abonnements."""
    subscriptions = db.query(Subscription).order_by(desc(Subscription.created_at)).all()
    response = []
    for sub in subscriptions:
        sub_resp = SubscriptionAdminResponse.from_orm(sub)
        if sub.user: # Vérifier si l'utilisateur associé existe
            sub_resp.user_name = f"{sub.user.first_name} {sub.user.last_name}"
            sub_resp.user_email = sub.user.email
        response.append(sub_resp)
    return response

@admin_router.post("/subscriptions", response_model=SubscriptionAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription_admin(sub_data: SubscriptionAdminCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Crée un nouvel abonnement et met à jour l'utilisateur associé."""
    user = db.query(User).get(sub_data.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    new_sub = Subscription(**sub_data.dict())
    
    # Mettre à jour l'utilisateur
    user.offer_type = sub_data.subscription_type
    user.subscription_start_date = sub_data.start_date
    user.subscription_end_date = sub_data.end_date
    user.is_active = (sub_data.status == "active" and sub_data.end_date >= datetime.utcnow())
    
    # Mettre à jour le quota (assurez-vous que QUOTAS est défini)
    user.scan_quota_limit = QUOTAS.get(sub_data.subscription_type, 0)
    user.scan_quota_used = 0 # Réinitialiser le quota utilisé lors de la création/MAJ
    user.quota_period_start = datetime.utcnow() # Réinitialiser la période

    try:
        db.add(new_sub)
        db.add(user) # Ajouter l'utilisateur mis à jour à la session
        db.commit()
        db.refresh(new_sub)
        db.refresh(user)
        print(f"Admin {current_admin.email} a créé un abonnement pour {user.email}")
        
        # Préparer la réponse
        sub_resp = SubscriptionAdminResponse.from_orm(new_sub)
        sub_resp.user_name = f"{user.first_name} {user.last_name}"
        sub_resp.user_email = user.email
        return sub_resp
        
    except Exception as e:
        db.rollback()
        print(f"Erreur DB POST /admin/subscriptions: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur serveur: {str(e)}")

@admin_router.put("/subscriptions/{subscription_id}", response_model=SubscriptionAdminResponse)
async def update_subscription_admin(subscription_id: int = Path(..., ge=1), sub_update: SubscriptionAdminUpdate = Body(...), db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Met à jour un abonnement et l'utilisateur associé."""
    subscription = db.query(Subscription).get(subscription_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Abonnement non trouvé")

    update_data = sub_update.dict(exclude_unset=True)
    updated = False

    for key, value in update_data.items():
        if hasattr(subscription, key) and value is not None:
            setattr(subscription, key, value)
            updated = True

    # Mettre à jour l'utilisateur associé si des champs pertinents changent
    user = subscription.user
    user_updated = False
    if user:
        if "subscription_type" in update_data:
            user.offer_type = update_data["subscription_type"]
            user.scan_quota_limit = QUOTAS.get(update_data["subscription_type"], 0)
            user_updated = True
        if "start_date" in update_data:
            user.subscription_start_date = update_data["start_date"]
            user_updated = True
        if "end_date" in update_data:
            user.subscription_end_date = update_data["end_date"]
            user_updated = True
        if "status" in update_data or "end_date" in update_data:
             # Recalculer is_active
             current_status = update_data.get("status", subscription.status)
             current_end_date = update_data.get("end_date", subscription.end_date)
             user.is_active = (current_status == "active" and current_end_date >= datetime.utcnow())
             user_updated = True
        if user_updated:
             db.add(user)

    if updated or user_updated:
        try:
            db.commit()
            db.refresh(subscription)
            if user and user_updated: db.refresh(user)
            print(f"Admin {current_admin.email} a mis à jour l'abonnement #{subscription_id}")
            
            # Préparer la réponse
            sub_resp = SubscriptionAdminResponse.from_orm(subscription)
            if user:
                sub_resp.user_name = f"{user.first_name} {user.last_name}"
                sub_resp.user_email = user.email
            return sub_resp
            
        except Exception as e:
            db.rollback()
            print(f"Erreur DB PUT /admin/subscriptions/{subscription_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur serveur: {str(e)}")
    else:
        # Si rien n'a été mis à jour, retourner l'abonnement actuel
        sub_resp = SubscriptionAdminResponse.from_orm(subscription)
        if user:
            sub_resp.user_name = f"{user.first_name} {user.last_name}"
            sub_resp.user_email = user.email
        return sub_resp
