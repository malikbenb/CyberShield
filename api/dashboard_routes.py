# Fichier : api/dashboard_routes.py

from flask import Blueprint, jsonify, request, send_from_directory, current_app, abort
from flask_login import login_required, current_user
from models import db, ScanHistory, Report, User, OFFER_TYPES, QUOTAS
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import ipaddress 
import os 
import json 
import uuid # Pour générer le batch_id

# Importer la tâche Celery
from tasks import run_scan

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# --- Routes existantes (Historique, Rapport, Profil) --- 

@dashboard_bp.route("/history", methods=["GET"])
@login_required
def get_scan_history():
    """Récupère l\'historique des scans pour l\'utilisateur connecté."""
    try:
        # Récupérer les scans individuels et les regrouper par batch_id si présent
        scans = ScanHistory.query.filter_by(user_id=current_user.id).order_by(ScanHistory.scan_start_time.desc()).all()
        
        history_data = []
        processed_batch_ids = set()

        for scan in scans:
            if scan.batch_id and scan.batch_id in processed_batch_ids:
                continue # Déjà traité dans un groupe

            if scan.batch_id                # C\'est un scan de groupe (Entreprise)                batch_scans = ScanHistory.query.filter_by(batch_id=scan.batch_id, user_id=current_user.id).order_by(ScanHistory.scan_start_time.asc()).all()
                if not batch_scans:
                    continue # Ne devrait pas arriver
                
                processed_batch_ids.add(scan.batch_id)
                # Déterminer le statut global du batch (ex: running si au moins un running, failed si au moins un failed, etc.)
                statuses = {s.status for s in batch_scans}
                batch_status = "completed"
                if "running" in statuses: batch_status = "running"
                elif "queued" in statuses: batch_status = "queued"
                elif "failed" in statuses: batch_status = "failed"
                elif "completed_with_errors" in statuses: batch_status = "completed_with_errors"
                
                # Calculer le score moyen ou max du batch ? Pour l\instant, on ne l\affiche pas au niveau batch.
                history_data.append({
                    "batch_id": scan.batch_id,
                    "scan_type": "enterprise",
                    "targets": [s.target_ip for s in batch_scans],
                    "start_time": batch_scans[0].scan_start_time.isoformat() if batch_scans[0].scan_start_time else None,
                    "status": batch_status,
                    "individual_scans": [
                        {
                            "id": s.id,
                            "target_ip": s.target_ip,
                            "status": s.status,
                            "score": s.vulnerability_score,
                            "report_available": Report.query.filter_by(scan_id=s.id).count() > 0
                        } for s in batch_scans
                    ]
                })
            else:
                # Scan individuel (Pro)
                history_data.append({
                    "id": scan.id,
                    "scan_type": "pro",
                    "target_ip": scan.target_ip,
                    "start_time": scan.scan_start_time.isoformat() if scan.scan_start_time else None,
                    "end_time": scan.scan_end_time.isoformat() if scan.scan_end_time else None,
                    "status": scan.status,
                    "score": scan.vulnerability_score,
                    "report_available": Report.query.filter_by(scan_id=scan.id).count() > 0
                })
                
        return jsonify(history_data), 200
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération de l\historique pour user {current_user.id}: {e}", exc_info=True)
        return jsonify({"message": "Erreur serveur lors de la récupération de l\historique"}), 500

@dashboard_bp.route("/report/<int:scan_id>", methods=["GET"])
@login_required
def get_scan_report(scan_id):
    """Récupère le rapport pour un scan spécifique (Pro ou Entreprise individuel)."""
    try:
        scan = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first()
        if not scan:
            abort(404, description="Scan non trouvé ou accès non autorisé")
        report = Report.query.filter_by(scan_id=scan_id).first()
        if not report:
             abort(404, description="Rapport non disponible pour ce scan")
        
        try:
            report_content_json = json.loads(report.content)
            report_data = {
                "scan_id": report.scan_id,
                "target_ip": scan.target_ip, # Ajouter l\IP cible
                "generated_at": report.generated_at.isoformat() if report.generated_at else None,
                "format": report.format,
                "content": report_content_json
            }
            return jsonify(report_data), 200
        except json.JSONDecodeError:
             current_app.logger.error(f"Erreur de décodage JSON pour le rapport du scan {scan_id}")
             # Retourner le contenu brut si le JSON est invalide
             report_data = {
                "scan_id": report.scan_id,
                "target_ip": scan.target_ip,
                "generated_at": report.generated_at.isoformat() if report.generated_at else None,
                "format": "text", 
                "content": report.content
            }
             return jsonify(report_data), 200

    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération du rapport {scan_id} pour user {current_user.id}: {e}", exc_info=True)
        return jsonify({"message": "Erreur serveur lors de la récupération du rapport"}), 500

@dashboard_bp.route("/profile", methods=["GET"])
@login_required
def get_profile():
    """Récupère les informations du profil, le statut de l\'abonnement et le quota."""
    user = User.query.get(current_user.id)
    if not user:
         abort(404, description="Utilisateur non trouvé")
         
    user.reset_quota_if_needed()
    db.session.commit() 
    
    return jsonify({
        "id": user.id,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "email": user.email,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "offer": {
            "type": user.offer_type,
            "subscription_active": user.is_active,
            "subscription_start": user.subscription_start_date.isoformat() if user.subscription_start_date else None,
            "subscription_end": user.subscription_end_date.isoformat() if user.subscription_end_date else None,
        },
        "quota": {
            "limit": user.scan_quota_limit,
            "used": user.scan_quota_used,
            "remaining": user.scan_quota_limit - user.scan_quota_used,
            "period_start": user.quota_period_start.isoformat()
        }
    }), 200

@dashboard_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    """Met à jour les informations du profil de l\\'utilisateur connecté.""""
    data = request.get_json()
    if not data:
        abort(400, description="Données manquantes")
        
    first_name = data.get("firstName")
    last_name = data.get("lastName")
    email = data.get("email")
    password = data.get("password")

    user = User.query.get(current_user.id)
    if not user:
        abort(404, description="Utilisateur non trouvé")

    updated = False
    if first_name is not None:
        if not isinstance(first_name, str) or len(first_name.strip()) == 0:
             abort(400, description="Prénom invalide")
        user.first_name = first_name.strip()
        updated = True
    if last_name is not None:
        if not isinstance(last_name, str) or len(last_name.strip()) == 0:
             abort(400, description="Nom invalide")
        user.last_name = last_name.strip()
        updated = True
    if email is not None:
        if not isinstance(email, str) or "@" not in email:
             abort(400, description="Email invalide")
        if user.email != email:
            if User.query.filter(User.email == email, User.id != user.id).first():
                abort(409, description="Cet email est déjà utilisé")
            user.email = email
            updated = True
    if password:
        if not isinstance(password, str) or len(password) < 8:
             abort(400, description="Le mot de passe doit contenir au moins 8 caractères")
        user.set_password(password)
        updated = True

    if updated:
        try:
            db.session.commit()
            current_app.logger.info(f"Profil utilisateur {user.id} mis à jour.")
            return jsonify({"message": "Profil mis à jour avec succès"}), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la mise à jour du profil user {user.id}: {e}", exc_info=True)
            abort(500, description="Erreur serveur lors de la mise à jour")
    else:
        return jsonify({"message": "Aucune modification fournie"}), 200

# --- Route pour Démarrer les Scans (Pro et Entreprise) --- 

@dashboard_bp.route("/scan/start", methods=["POST"])
@login_required
def start_scan():
    """Démarre un nouveau scan (Pro ou Entreprise) en vérifiant l\offre et le quota."""
    data = request.get_json()
    if not data:
        abort(400, description="Données manquantes")

    target_ips_input = data.get("target_ips") # Peut être une string (Pro) ou une liste (Entreprise)
    if not target_ips_input:
         abort(400, description="Adresse(s) IP cible(s) manquante(s)")

    user = User.query.get(current_user.id)
    if not user:
         abort(404, description="Utilisateur non trouvé") # Ne devrait pas arriver avec @login_required

    # Vérifier si l\abonnement est actif
    if not user.is_active:
        abort(403, description="Votre abonnement n\est pas actif. Veuillez renouveler votre abonnement.")

    target_ips = []
    is_enterprise_scan = False
    
    if isinstance(target_ips_input, list):
        # Potentiellement un scan Entreprise
        if user.offer_type != "enterprise":
            abort(403, description="Votre offre ne permet pas de lancer des scans sur plusieurs IPs.")
        if len(target_ips_input) > QUOTAS["enterprise"]:
             abort(400, description=f"Vous ne pouvez pas scanner plus de {QUOTAS[\"enterprise\"]} IPs à la fois.")
        target_ips = target_ips_input
        is_enterprise_scan = True
        scan_type = "enterprise"
        num_scans_requested = len(target_ips)
    elif isinstance(target_ips_input, str):
        # Scan Pro (ou Entreprise avec une seule IP)
        if user.offer_type not in ["pro", "enterprise"]:
             abort(403, description="Votre offre ne permet pas de lancer ce type de scan.")
        target_ips = [target_ips_input]
        scan_type = "pro" # Même si l\utilisateur est Entreprise, un scan unique est traité comme Pro pour la simplicité du quota
        num_scans_requested = 1
    else:
        abort(400, description="Format d\entrée pour target_ips invalide.")

    # Valider les adresses IP
    valid_ips = []
    invalid_ips = []
    for ip_str in target_ips:
        try:
            ipaddress.ip_address(ip_str)
            valid_ips.append(ip_str)
        except ValueError:
            invalid_ips.append(ip_str)
    
    if invalid_ips:
        abort(400, description=f"Format d\adresse IP invalide pour : {\", \".join(invalid_ips)}")
    if not valid_ips:
         abort(400, description="Aucune adresse IP valide fournie.")

    # --- Vérification du Quota --- 
    if not user.has_quota_remaining(requested_scans=num_scans_requested):
        current_app.logger.warning(f"Quota de scan insuffisant pour l\utilisateur {user.id} (demandé: {num_scans_requested}, restant: {user.scan_quota_limit - user.scan_quota_used})")
        reset_date = user.quota_period_start + timedelta(days=30)
        abort(429, description=f"Quota insuffisant pour lancer {num_scans_requested} scan(s). Restant: {user.scan_quota_limit - user.scan_quota_used}. Réinitialisation le {reset_date.strftime(\"%Y-%m-%d\")}.")

    # --- Si Quota OK, continuer --- 
    batch_id = None
    if is_enterprise_scan:
        batch_id = str(uuid.uuid4()) # Générer un ID unique pour le lot
        
    scan_ids = []
    task_ids = []
    
    try:
        # Incrémenter le quota AVANT de créer les scans
        user.increment_quota_used(count=num_scans_requested)
        db.session.add(user) # Ajouter l\utilisateur à la session pour sauvegarder le quota

        # Créer les enregistrements ScanHistory
        new_scans = []
        for ip in valid_ips:
            new_scan = ScanHistory(
                user_id=user.id,
                batch_id=batch_id, # Sera None pour les scans Pro
                scan_type=scan_type,
                target_ip=ip,
                status="queued",
                scan_start_time=datetime.utcnow()
            )
            db.session.add(new_scan)
            new_scans.append(new_scan)
            
        # Commit l\incrémentation du quota et la création des scans ensemble
        db.session.commit()
        scan_ids = [s.id for s in new_scans]
        current_app.logger.info(f"Quota incrémenté ({num_scans_requested}) et {len(scan_ids)} ScanHistory créés pour user {user.id}. Batch ID: {batch_id}")

        # Lancer les tâches Celery après le commit réussi
        for scan_obj in new_scans:
            try:
                task_result = run_scan.delay(scan_obj.id, scan_obj.target_ip)
                scan_obj.celery_task_id = task_result.id
                task_ids.append(task_result.id)
            except Exception as celery_err:
                 # Si le lancement d\une tâche échoue, logguer et continuer avec les autres
                 current_app.logger.error(f"Erreur lors du lancement de la tâche Celery pour scan {scan_obj.id}: {celery_err}", exc_info=True)
                 scan_obj.status = "failed" # Marquer ce scan spécifique comme échoué
                 scan_obj.celery_task_id = None
                 # Ne pas annuler les autres scans déjà lancés
        
        # Sauvegarder les IDs de tâches Celery et les statuts échoués
        try:
            db.session.commit()
            current_app.logger.info(f"{len(task_ids)} tâches Celery lancées et IDs sauvegardés pour Batch ID: {batch_id}")
        except Exception as db_err_celery:
             db.session.rollback()
             current_app.logger.error(f"Erreur lors de la sauvegarde des IDs Celery pour Batch ID {batch_id}: {db_err_celery}", exc_info=True)
             # Les tâches sont lancées mais les IDs ne sont pas sauvegardés

        response_data = {
            "message": f"{len(valid_ips)} scan(s) démarré(s) avec succès", 
            "scan_ids": scan_ids,
            "task_ids": task_ids,
            "batch_id": batch_id, # Sera None pour les scans Pro
            "quota_remaining": user.scan_quota_limit - user.scan_quota_used
        }
        return jsonify(response_data), 202

    except Exception as e:
        db.session.rollback() # Annule l\incrémentation du quota et la création des scans
        current_app.logger.error(f"Erreur majeure lors du démarrage du scan batch {batch_id} pour user {user.id}: {e}", exc_info=True)
        abort(500, description="Erreur serveur lors du démarrage du scan")

# --- Route pour Télécharger les Scanners Pro --- 

@dashboard_bp.route("/download/scanner/<os_type>", methods=["GET"])
@login_required
def download_pro_scanner(os_type):
    """Permet à un utilisateur authentifié (Pro ou Entreprise) de télécharger le scanner Pro."""
    user = User.query.get(current_user.id)
    if not user or user.offer_type not in ["pro", "enterprise"]:
        abort(403, description="Accès non autorisé à cette ressource.")
        
    if not user.is_active:
         abort(403, description="Votre abonnement n\est pas actif.")

    scanner_directory = os.path.abspath(os.path.join(current_app.root_path, "..", "scanners", "pro")) # Ajuster le chemin si nécessaire
    # Créer le répertoire s\il n\existe pas (pour les placeholders)
    os.makedirs(scanner_directory, exist_ok=True)
    
    filename_map = {
        "linux": "cybershield_pro_scanner_linux.sh",
        "macos": "cybershield_pro_scanner_macos.sh",
        "windows": "cybershield_pro_scanner_windows.bat"
    }
    
    if os_type not in filename_map:
        abort(400, description="Type de système d\exploitation non valide.")
        
    filename = filename_map[os_type]
    file_path = os.path.join(scanner_directory, filename)

    # Créer un fichier placeholder s\il n\existe pas
    if not os.path.isfile(file_path):
        try:
            with open(file_path, "w") as f:
                f.write(f"#!/bin/bash\n# Placeholder for CyberShield Pro Scanner ({os_type})\n# TODO: Implement actual scanner logic\necho \"CyberShield Pro Scanner ({os_type}) - Placeholder\"\n")
            if os_type == "linux" or os_type == "macos":
                 os.chmod(file_path, 0o755) # Rendre exécutable
            current_app.logger.warning(f"Fichier scanner placeholder créé: {file_path}")
        except Exception as placeholder_err:
             current_app.logger.error(f"Impossible de créer le fichier scanner placeholder {file_path}: {placeholder_err}")
             abort(500, description="Erreur serveur lors de la préparation du fichier scanner.")

    try:
        current_app.logger.info(f"Utilisateur {current_user.id} télécharge le scanner {filename}")
        return send_from_directory(scanner_directory, filename, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l\envoi du fichier {filename} pour user {current_user.id}: {e}", exc_info=True)
        abort(500, description="Erreur serveur lors du téléchargement du fichier.")

# Fonction pour initialiser les routes
def init_dashboard_routes(app):
    app.register_blueprint(dashboard_bp)
    current_app.logger.info("Routes du Dashboard initialisées (incluant logique Entreprise).")

