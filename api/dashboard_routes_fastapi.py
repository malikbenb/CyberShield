from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Union, Dict, Any
from datetime import datetime, timedelta
import ipaddress
import os
import json
import uuid

# Importer les modèles SQLAlchemy, la session DB, et l'authentification
from models_fastapi import User, ScanHistory, Report, OFFER_TYPES, QUOTAS # Utiliser models_fastapi au lieu de models
from database import get_db
from auth_fastapi import get_current_user # Utilise l'authentification JWT

# Importer la tâche Celery (en supposant qu'elle est définie correctement)
from tasks import run_scan

# --- Modèles Pydantic pour la validation et la sérialisation ---

class ScanBase(BaseModel):
    target_ip: str
    status: str
    score: Optional[float] = None

class IndividualScanInfo(ScanBase):
    id: int
    report_available: bool

class BatchScanInfo(BaseModel):
    batch_id: str
    scan_type: str = "enterprise"
    targets: List[str]
    start_time: Optional[datetime] = None
    status: str
    individual_scans: List[IndividualScanInfo]

class ProScanInfo(ScanBase):
    id: int
    scan_type: str = "pro"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    report_available: bool

# Union pour représenter soit un scan Pro soit un batch Entreprise
ScanHistoryResponseItem = Union[ProScanInfo, BatchScanInfo]

class ReportContent(BaseModel):
    # Définissez ici la structure attendue du contenu JSON du rapport
    # Exemple :
    summary: Optional[str] = None
    vulnerabilities: Optional[List[Dict[str, Any]]] = None
    # Adaptez selon le contenu réel généré par vos scanners
    pass

class ReportResponse(BaseModel):
    scan_id: int
    target_ip: str
    generated_at: Optional[datetime] = None
    format: str
    content: Union[ReportContent, str] # Peut être JSON structuré ou texte brut

class OfferInfo(BaseModel):
    type: str
    subscription_active: bool
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None

class QuotaInfo(BaseModel):
    limit: int
    used: int
    remaining: int
    period_start: datetime

class ProfileResponse(BaseModel):
    id: int
    firstName: str = Field(..., alias="first_name")
    lastName: str = Field(..., alias="last_name")
    email: EmailStr
    createdAt: Optional[datetime] = Field(None, alias="created_at")
    offer: OfferInfo
    quota: QuotaInfo

    class Config:
        orm_mode = True
        allow_population_by_field_name = True # Permet d'utiliser les alias

class ProfileUpdate(BaseModel):
    firstName: Optional[str] = Field(None, alias="first_name")
    lastName: Optional[str] = Field(None, alias="last_name")
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)

class ScanStartRequest(BaseModel):
    target_ips: Union[str, List[str]] # Accepte une IP (Pro) ou une liste (Entreprise)

class ScanStartResponse(BaseModel):
    message: str
    scan_ids: List[int]
    task_ids: List[str]
    batch_id: Optional[str] = None
    quota_remaining: int

# --- Router FastAPI ---
dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Tableau de Bord"],
    dependencies=[Depends(get_current_user)], # Toutes les routes ici nécessitent authentification
    responses={404: {"description": "Non trouvé"}},
)

# --- Conversion des Routes ---

@dashboard_router.get("/history", response_model=List[ScanHistoryResponseItem])
async def get_scan_history_fastapi(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Récupère l'historique des scans pour l'utilisateur connecté."""
    try:
        scans = db.query(ScanHistory).filter(ScanHistory.user_id == current_user.id).order_by(ScanHistory.scan_start_time.desc()).all()
        
        history_data = []
        processed_batch_ids = set()

        for scan in scans:
            if scan.batch_id and scan.batch_id in processed_batch_ids:
                continue

            report_count = db.query(Report).filter(Report.scan_id == scan.id).count()
            report_available = report_count > 0

            if scan.batch_id:
                if scan.batch_id in processed_batch_ids: continue # Double check
                
                batch_scans_db = db.query(ScanHistory).filter(
                    ScanHistory.batch_id == scan.batch_id, 
                    ScanHistory.user_id == current_user.id
                ).order_by(ScanHistory.scan_start_time.asc()).all()
                
                if not batch_scans_db:
                    continue
                
                processed_batch_ids.add(scan.batch_id)
                statuses = {s.status for s in batch_scans_db}
                batch_status = "completed"
                if "running" in statuses: batch_status = "running"
                elif "queued" in statuses: batch_status = "queued"
                elif "failed" in statuses: batch_status = "failed"
                elif "completed_with_errors" in statuses: batch_status = "completed_with_errors"

                individual_scans_info = []
                for s in batch_scans_db:
                     s_report_count = db.query(Report).filter(Report.scan_id == s.id).count()
                     individual_scans_info.append(IndividualScanInfo(
                         id=s.id,
                         target_ip=s.target_ip,
                         status=s.status,
                         score=s.vulnerability_score,
                         report_available=s_report_count > 0
                     ))

                history_data.append(BatchScanInfo(
                    batch_id=scan.batch_id,
                    targets=[s.target_ip for s in batch_scans_db],
                    start_time=batch_scans_db[0].scan_start_time,
                    status=batch_status,
                    individual_scans=individual_scans_info
                ))
            else:
                # Scan individuel (Pro)
                history_data.append(ProScanInfo(
                    id=scan.id,
                    target_ip=scan.target_ip,
                    start_time=scan.scan_start_time,
                    end_time=scan.scan_end_time,
                    status=scan.status,
                    score=scan.vulnerability_score,
                    report_available=report_available
                ))
                
        return history_data
    except Exception as e:
        # Loggez l'erreur e de manière appropriée (ex: avec logging)
        print(f"Erreur /history user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur serveur lors de la récupération de l'historique")

@dashboard_router.get("/report/{scan_id}", response_model=ReportResponse)
async def get_scan_report_fastapi(scan_id: int = Path(..., title="ID du Scan", ge=1), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Récupère le rapport pour un scan spécifique."""
    try:
        scan = db.query(ScanHistory).filter(ScanHistory.id == scan_id, ScanHistory.user_id == current_user.id).first()
        if not scan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan non trouvé ou accès non autorisé")
        
        report = db.query(Report).filter(Report.scan_id == scan_id).first()
        if not report:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapport non disponible pour ce scan")
        
        report_content_parsed = report.content
        report_format = report.format
        try:
            # Essayer de parser comme JSON si le format est json
            if report.format.lower() == "json":
                report_content_parsed = json.loads(report.content)
                # Optionnel : Valider avec Pydantic si ReportContent est défini
                # report_content_parsed = ReportContent.parse_raw(report.content)
            # Si ce n'est pas json, on garde le texte brut
        except json.JSONDecodeError:
             print(f"Avertissement : Erreur de décodage JSON pour rapport scan {scan_id}, retour brut.")
             report_format = "text" # Forcer le format texte si le JSON est invalide
             report_content_parsed = report.content # Retourner le contenu brut

        return ReportResponse(
            scan_id=report.scan_id,
            target_ip=scan.target_ip,
            generated_at=report.generated_at,
            format=report_format,
            content=report_content_parsed
        )

    except HTTPException as http_exc:
        raise http_exc # Re-lever les exceptions HTTP déjà gérées
    except Exception as e:
        print(f"Erreur /report/{scan_id} user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur serveur lors de la récupération du rapport")

@dashboard_router.get("/profile", response_model=ProfileResponse)
async def get_profile_fastapi(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Récupère les informations du profil, le statut de l'abonnement et le quota."""
    user = db.query(User).get(current_user.id) # Utiliser get() est plus direct avec la clé primaire
    if not user:
         # Ne devrait pas arriver car get_current_user lève une exception si non trouvé
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
         
    try:
        user.reset_quota_if_needed() # Supposant que cette méthode existe et fonctionne avec SQLAlchemy standard
        db.commit() 
        db.refresh(user) # Rafraîchir l'état de l'utilisateur depuis la DB
    except Exception as e:
        db.rollback()
        print(f"Erreur reset_quota_if_needed user {user.id}: {e}")
        # Peut-être ne pas bloquer ici, mais logger l'erreur

    # Calculer le quota restant
    quota_remaining = user.scan_quota_limit - user.scan_quota_used

    return ProfileResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        created_at=user.created_at,
        offer=OfferInfo(
            type=user.offer_type,
            subscription_active=user.is_active, # Supposant un champ is_active
            subscription_start=user.subscription_start_date,
            subscription_end=user.subscription_end_date,
        ),
        quota=QuotaInfo(
            limit=user.scan_quota_limit,
            used=user.scan_quota_used,
            remaining=quota_remaining,
            period_start=user.quota_period_start
        )
    )

@dashboard_router.put("/profile", response_model=ProfileResponse)
async def update_profile_fastapi(profile_data: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Met à jour les informations du profil de l'utilisateur connecté."""
    user = db.query(User).get(current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    update_data = profile_data.dict(exclude_unset=True) # Obtenir seulement les champs fournis
    updated = False

    if "firstName" in update_data:
        user.first_name = update_data["firstName"].strip()
        updated = True
    if "lastName" in update_data:
        user.last_name = update_data["lastName"].strip()
        updated = True
    if "email" in update_data:
        new_email = update_data["email"]
        if user.email != new_email:
            existing_user = db.query(User).filter(User.email == new_email, User.id != user.id).first()
            if existing_user:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cet email est déjà utilisé")
            user.email = new_email
            updated = True
    if "password" in update_data:
        # Importer get_password_hash depuis auth_fastapi ou le définir ici
        from auth_fastapi import get_password_hash 
        user.hashed_password = get_password_hash(update_data["password"]) # Assurez-vous que le modèle a hashed_password
        updated = True

    if updated:
        try:
            db.commit()
            db.refresh(user)
            print(f"Profil utilisateur {user.id} mis à jour.")
            # Retourner le profil mis à jour
            # Recalculer le quota restant pour la réponse
            quota_remaining = user.scan_quota_limit - user.scan_quota_used
            return ProfileResponse(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                created_at=user.created_at,
                offer=OfferInfo(
                    type=user.offer_type,
                    subscription_active=user.is_active,
                    subscription_start=user.subscription_start_date,
                    subscription_end=user.subscription_end_date,
                ),
                quota=QuotaInfo(
                    limit=user.scan_quota_limit,
                    used=user.scan_quota_used,
                    remaining=quota_remaining,
                    period_start=user.quota_period_start
                )
            )
        except Exception as e:
            db.rollback()
            print(f"Erreur DB /profile PUT user {user.id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur serveur lors de la mise à jour")
    else:
        # Si rien n'a été mis à jour, retourner le profil actuel
        quota_remaining = user.scan_quota_limit - user.scan_quota_used
        return ProfileResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            created_at=user.created_at,
            offer=OfferInfo(
                type=user.offer_type,
                subscription_active=user.is_active,
                subscription_start=user.subscription_start_date,
                subscription_end=user.subscription_end_date,
            ),
            quota=QuotaInfo(
                limit=user.scan_quota_limit,
                used=user.scan_quota_used,
                remaining=quota_remaining,
                period_start=user.quota_period_start
            )
        )

@dashboard_router.post("/scan/start", response_model=ScanStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scan_fastapi(scan_request: ScanStartRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Démarre un nouveau scan (Pro ou Entreprise) en vérifiant l'offre et le quota."""
    user = db.query(User).get(current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Votre abonnement n'est pas actif.")

    target_ips_input = scan_request.target_ips
    target_ips = []
    is_enterprise_scan = False
    scan_type = ""
    num_scans_requested = 0

    if isinstance(target_ips_input, list):
        if user.offer_type != "enterprise":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Votre offre ne permet pas de lancer des scans sur plusieurs IPs.")
        # Assurez-vous que QUOTAS est défini et accessible
        if len(target_ips_input) > QUOTAS.get("enterprise", 20): # Utiliser .get avec une valeur par défaut
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vous ne pouvez pas scanner plus de {QUOTAS.get('enterprise', 20)} IPs à la fois.")
        target_ips = target_ips_input
        is_enterprise_scan = True
        scan_type = "enterprise"
        num_scans_requested = len(target_ips)
    elif isinstance(target_ips_input, str):
        # Scan Pro (une seule IP)
        if user.offer_type not in ["pro", "enterprise"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Votre offre ne permet pas de lancer des scans Pro.")
        target_ips = [target_ips_input]
        scan_type = "pro"
        num_scans_requested = 1
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format de cible invalide. Fournissez une IP ou une liste d'IPs.")

    # Valider les adresses IP
    invalid_ips = []
    for ip in target_ips:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            invalid_ips.append(ip)
    
    if invalid_ips:
        invalid_ips_str = ", ".join(invalid_ips)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Format d'adresse IP invalide pour : {invalid_ips_str}")

    # Vérifier le quota
    if user.scan_quota_used + num_scans_requested > user.scan_quota_limit:
        # Calculer la date de réinitialisation du quota
        reset_date = user.quota_period_start + timedelta(days=30)  # Supposant une période de 30 jours
        reset_date_str = reset_date.strftime("%Y-%m-%d")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
                           detail=f"Quota insuffisant pour lancer {num_scans_requested} scan(s). Restant: {user.scan_quota_limit - user.scan_quota_used}. Réinitialisation le {reset_date_str}.")

    # Créer un ID de lot pour les scans Enterprise
    batch_id = str(uuid.uuid4()) if is_enterprise_scan else None

    # Créer les entrées de scan dans la base de données
    scan_ids = []
    task_ids = []

    try:
        for target_ip in target_ips:
            # Créer l'entrée de scan
            new_scan = ScanHistory(
                user_id=user.id,
                target_ip=target_ip,
                scan_type=scan_type,
                status="queued",
                batch_id=batch_id
            )
            db.add(new_scan)
            db.flush()  # Pour obtenir l'ID généré
            scan_ids.append(new_scan.id)
            
            # Lancer la tâche Celery
            task = run_scan.delay(new_scan.id, target_ip, scan_type)
            task_ids.append(task.id)
            
            # Mettre à jour l'entrée avec l'ID de tâche
            new_scan.task_id = task.id
            db.add(new_scan)
        
        # Mettre à jour le quota utilisé
        user.scan_quota_used += num_scans_requested
        db.add(user)
        
        db.commit()
        
        # Calculer le quota restant après cette opération
        quota_remaining = user.scan_quota_limit - user.scan_quota_used
        
        return ScanStartResponse(
            message=f"Scan{'s' if num_scans_requested > 1 else ''} lancé{'s' if num_scans_requested > 1 else ''} avec succès",
            scan_ids=scan_ids,
            task_ids=task_ids,
            batch_id=batch_id,
            quota_remaining=quota_remaining
        )
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors du lancement du scan pour user {user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur serveur lors du lancement du scan")
