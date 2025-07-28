from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, cast, Date
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json

from models_fastapi import User, ScanHistory, Report, Subscription
from database import get_db
from auth_fastapi import get_current_user

# Router pour les statistiques
stats_router = APIRouter(prefix="/stats", tags=["statistics"])

class DownloadStats(BaseModel):
    total_downloads: int
    downloads_by_date: Dict[str, int]
    downloads_by_type: Dict[str, int]
    recent_downloads: List[Dict[str, Any]]

class ScanStats(BaseModel):
    total_scans: int
    scans_by_date: Dict[str, int]
    scans_by_status: Dict[str, int]
    scans_by_type: Dict[str, int]
    vulnerability_score_avg: float
    recent_scans: List[Dict[str, Any]]

@stats_router.get("/downloads", response_model=DownloadStats)
async def get_download_stats(
    days: Optional[int] = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les statistiques de téléchargement pour l\"utilisateur connecté.
    """
    # Vérifier si l\"utilisateur est administrateur pour les statistiques globales
    is_admin = current_user.is_admin
    
    # Date de début pour la période de statistiques
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Créer une table de téléchargements si elle n\"existe pas déjà
    # Note: Dans une implémentation réelle, cette table devrait être créée via une migration
    # Cette partie est simplifiée pour la démonstration et devrait être gérée par Alembic ou un outil similaire en production.
    try:
        db.execute("""
        CREATE TABLE IF NOT EXISTS download_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES \"user\"(id),
            download_type VARCHAR(50) NOT NULL,
            file_path VARCHAR(255) NOT NULL,
            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la création de la table download_history: {e}")
        # Ne pas lever d\"exception ici pour ne pas bloquer l\"API si la table existe déjà
    
    # Requête de base pour les téléchargements
    base_query = db.query(
        func.count().label("total"),
        cast(func.date_trunc('day', "downloaded_at"), Date).label("date"),
        "download_type"
    ).filter(
        "downloaded_at" >= start_date
    )
    
    # Filtrer par utilisateur si non admin
    if not is_admin:
        base_query = base_query.filter(ScanHistory.user_id == current_user.id) # Correction: utiliser ScanHistory.user_id
    
    # Grouper par date et type
    downloads_by_date_type = base_query.group_by(
        cast(func.date_trunc('day', "downloaded_at"), Date),
        "download_type"
    ).all()
    
    # Formater les résultats
    total_downloads = 0
    downloads_by_date = {}
    downloads_by_type = {"free": 0, "pro": 0, "enterprise": 0}
    
    for result in downloads_by_date_type:
        total_downloads += result.total
        date_str = result.date.strftime("%Y-%m-%d")
        
        if date_str not in downloads_by_date:
            downloads_by_date[date_str] = 0
        
        downloads_by_date[date_str] += result.total
        downloads_by_type[result.download_type] += result.total
    
    # Récupérer les téléchargements récents
    recent_downloads_query = db.query(DownloadHistory).filter(
        DownloadHistory.downloaded_at >= start_date
    )
    
    if not is_admin:
        recent_downloads_query = recent_downloads_query.filter(DownloadHistory.user_id == current_user.id)
    
    recent_downloads = recent_downloads_query.order_by(DownloadHistory.downloaded_at.desc()).limit(10).all()
    
    # Formater les téléchargements récents
    recent_downloads_formatted = []
    for download in recent_downloads:
        user = db.query(User).filter(User.id == download.user_id).first()
        recent_downloads_formatted.append({
            "id": download.id,
            "user": f"{user.first_name} {user.last_name}" if user else "Unknown",
            "type": download.download_type,
            "file": download.file_path,
            "date": download.downloaded_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return DownloadStats(
        total_downloads=total_downloads,
        downloads_by_date=downloads_by_date,
        downloads_by_type=downloads_by_type,
        recent_downloads=recent_downloads_formatted
    )

@stats_router.get("/scans", response_model=ScanStats)
async def get_scan_stats(
    days: Optional[int] = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les statistiques de scan pour l\"utilisateur connecté.
    """
    # Vérifier si l\"utilisateur est administrateur pour les statistiques globales
    is_admin = current_user.is_admin
    
    # Date de début pour la période de statistiques
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Requête de base pour les scans
    base_query = db.query(ScanHistory).filter(
        ScanHistory.scan_start_time >= start_date
    )
    
    # Filtrer par utilisateur si non admin
    if not is_admin:
        base_query = base_query.filter(ScanHistory.user_id == current_user.id)
    
    # Récupérer tous les scans pour la période
    scans = base_query.all()
    
    # Calculer les statistiques
    total_scans = len(scans)
    scans_by_date = {}
    scans_by_status = {}
    scans_by_type = {}
    vulnerability_scores = []
    
    for scan in scans:
        # Par date
        date_str = scan.scan_start_time.strftime("%Y-%m-%d")
        if date_str not in scans_by_date:
            scans_by_date[date_str] = 0
        scans_by_date[date_str] += 1
        
        # Par statut
        if scan.status not in scans_by_status:
            scans_by_status[scan.status] = 0
        scans_by_status[scan.status] += 1
        
        # Par type
        if scan.scan_type not in scans_by_type:
            scans_by_type[scan.scan_type] = 0
        scans_by_type[scan.scan_type] += 1
        
        # Score de vulnérabilité
        if scan.vulnerability_score is not None:
            vulnerability_scores.append(scan.vulnerability_score)
    
    # Calculer la moyenne des scores de vulnérabilité
    vulnerability_score_avg = sum(vulnerability_scores) / len(vulnerability_scores) if vulnerability_scores else 0
    
    # Récupérer les scans récents avec leurs rapports
    recent_scans = base_query.order_by(ScanHistory.scan_start_time.desc()).limit(10).all()
    
    # Formater les scans récents
    recent_scans_formatted = []
    for scan in recent_scans:
        user = db.query(User).filter(User.id == scan.user_id).first()
        report = db.query(Report).filter(Report.scan_id == scan.id).first()
        
        recent_scans_formatted.append({
            "id": scan.id,
            "user": f"{user.first_name} {user.last_name}" if user else "Unknown",
            "target_ip": scan.target_ip,
            "type": scan.scan_type,
            "status": scan.status,
            "score": scan.vulnerability_score,
            "start_time": scan.scan_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": scan.scan_end_time.strftime("%Y-%m-%d %H:%M:%S") if scan.scan_end_time else None,
            "has_report": report is not None
        })
    
    return ScanStats(
        total_scans=total_scans,
        scans_by_date=scans_by_date,
        scans_by_status=scans_by_status,
        scans_by_type=scans_by_type,
        vulnerability_score_avg=vulnerability_score_avg,
        recent_scans=recent_scans_formatted
    )
