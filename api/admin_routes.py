# Fichier : api/admin_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, abort, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import desc
import json

from models import db, User, ScanHistory, Report, Subscription
from auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Routes API pour l'interface d'administration

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Récupère la liste des utilisateurs pour l'interface d'administration"""
    users = User.query.all()
    result = []
    
    for user in users:
        user_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'offer_type': user.offer_type,
            'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'subscription_start_date': user.subscription_start_date.isoformat() if user.subscription_start_date else None,
            'subscription_end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None,
            'scan_quota_limit': user.scan_quota_limit,
            'scan_quota_used': user.scan_quota_used,
            'is_active': user.is_active
        }
        result.append(user_data)
    
    return jsonify(result)

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    """Récupère les détails d'un utilisateur spécifique"""
    user = User.query.get_or_404(user_id)
    
    # Récupérer l'historique des scans de l'utilisateur
    scans = ScanHistory.query.filter_by(user_id=user_id).order_by(desc(ScanHistory.created_at)).all()
    scan_history = []
    
    for scan in scans:
        scan_data = {
            'id': scan.id,
            'target_ip': scan.target_ip,
            'scan_type': scan.scan_type,
            'status': scan.status,
            'created_at': scan.created_at.isoformat(),
            'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
            'score': scan.score
        }
        scan_history.append(scan_data)
    
    user_data = {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'offer_type': user.offer_type,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'subscription_start_date': user.subscription_start_date.isoformat() if user.subscription_start_date else None,
        'subscription_end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None,
        'scan_quota_limit': user.scan_quota_limit,
        'scan_quota_used': user.scan_quota_used,
        'is_active': user.is_active,
        'scan_history': scan_history
    }
    
    return jsonify(user_data)

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Met à jour les informations d'un utilisateur"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'email' in data:
        user.email = data['email']
    if 'offer_type' in data:
        user.offer_type = data['offer_type']
    if 'subscription_start_date' in data and data['subscription_start_date']:
        user.subscription_start_date = datetime.fromisoformat(data['subscription_start_date'])
    if 'subscription_end_date' in data and data['subscription_end_date']:
        user.subscription_end_date = datetime.fromisoformat(data['subscription_end_date'])
    if 'scan_quota_limit' in data:
        user.scan_quota_limit = data['scan_quota_limit']
    if 'scan_quota_used' in data:
        user.scan_quota_used = data['scan_quota_used']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'is_admin' in data:
        # Vérifier qu'on ne retire pas les droits admin au dernier admin
        if not data['is_admin'] and user.is_admin:
            admin_count = User.query.filter_by(is_admin=True).count()
            if admin_count <= 1:
                return jsonify({'error': 'Impossible de retirer les droits admin au dernier administrateur'}), 400
        user.is_admin = data['is_admin']
    
    try:
        db.session.commit()
        current_app.logger.info(f"Admin {current_user.email} a mis à jour l'utilisateur {user.email}")
        return jsonify({'message': 'Utilisateur mis à jour avec succès'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la mise à jour de l'utilisateur: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """Réinitialise le mot de passe d'un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    # Ici, vous pourriez implémenter l'envoi d'un email avec un lien de réinitialisation
    # Pour l'instant, on simule juste la réinitialisation
    
    current_app.logger.info(f"Admin {current_user.email} a demandé la réinitialisation du mot de passe pour {user.email}")
    return jsonify({'message': 'Demande de réinitialisation de mot de passe envoyée'})

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Supprime un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    # Vérifier qu'on ne supprime pas le dernier admin
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            return jsonify({'error': 'Impossible de supprimer le dernier administrateur'}), 400
    
    try:
        db.session.delete(user)
        db.session.commit()
        current_app.logger.info(f"Admin {current_user.email} a supprimé l'utilisateur {user.email}")
        return jsonify({'message': 'Utilisateur supprimé avec succès'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la suppression de l'utilisateur: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/subscriptions', methods=['GET'])
@login_required
@admin_required
def get_subscriptions():
    """Récupère la liste des abonnements"""
    subscriptions = Subscription.query.order_by(desc(Subscription.created_at)).all()
    result = []
    
    for sub in subscriptions:
        user = User.query.get(sub.user_id)
        sub_data = {
            'id': sub.id,
            'user_id': sub.user_id,
            'user_name': f"{user.first_name} {user.last_name}" if user else "Utilisateur inconnu",
            'user_email': user.email if user else "Email inconnu",
            'subscription_type': sub.subscription_type,
            'start_date': sub.start_date.isoformat(),
            'end_date': sub.end_date.isoformat(),
            'price': sub.price,
            'status': sub.status,
            'created_at': sub.created_at.isoformat()
        }
        result.append(sub_data)
    
    return jsonify(result)

@admin_bp.route('/subscriptions', methods=['POST'])
@login_required
@admin_required
def create_subscription():
    """Crée un nouvel abonnement"""
    data = request.get_json()
    
    # Vérifier que l'utilisateur existe
    user = User.query.get(data.get('user_id'))
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    # Créer l'abonnement
    subscription = Subscription(
        user_id=data.get('user_id'),
        subscription_type=data.get('subscription_type'),
        start_date=datetime.fromisoformat(data.get('start_date')),
        end_date=datetime.fromisoformat(data.get('end_date')),
        price=data.get('price'),
        status='active',
        notes=data.get('notes', '')
    )
    
    # Mettre à jour les informations d'abonnement de l'utilisateur
    user.offer_type = data.get('subscription_type')
    user.subscription_start_date = datetime.fromisoformat(data.get('start_date'))
    user.subscription_end_date = datetime.fromisoformat(data.get('end_date'))
    
    # Définir le quota en fonction du type d'abonnement
    if data.get('subscription_type') == 'pro':
        user.scan_quota_limit = 10
    elif data.get('subscription_type') == 'enterprise':
        user.scan_quota_limit = 20
    else:
        user.scan_quota_limit = 0
    
    # Réinitialiser le quota utilisé
    user.scan_quota_used = 0
    
    try:
        db.session.add(subscription)
        db.session.commit()
        current_app.logger.info(f"Admin {current_user.email} a créé un abonnement pour {user.email}")
        return jsonify({
            'message': 'Abonnement créé avec succès',
            'subscription_id': subscription.id
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la création de l'abonnement: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/subscriptions/<int:subscription_id>', methods=['PUT'])
@login_required
@admin_required
def update_subscription(subscription_id):
    """Met à jour un abonnement"""
    subscription = Subscription.query.get_or_404(subscription_id)
    data = request.get_json()
    
    if 'subscription_type' in data:
        subscription.subscription_type = data['subscription_type']
    if 'start_date' in data:
        subscription.start_date = datetime.fromisoformat(data['start_date'])
    if 'end_date' in data:
        subscription.end_date = datetime.fromisoformat(data['end_date'])
    if 'price' in data:
        subscription.price = data['price']
    if 'status' in data:
        subscription.status = data['status']
    if 'notes' in data:
        subscription.notes = data['notes']
    
    # Mettre à jour les informations d'abonnement de l'utilisateur
    user = User.query.get(subscription.user_id)
    if user:
        if 'subscription_type' in data:
            user.offer_type = data['subscription_type']
        if 'start_date' in data:
            user.subscription_start_date = datetime.fromisoformat(data['start_date'])
        if 'end_date' in data:
            user.subscription_end_date = datetime.fromisoformat(data['end_date'])
        
        # Mettre à jour le quota si le type d'abonnement change
        if 'subscription_type' in data:
            if data['subscription_type'] == 'pro':
                user.scan_quota_limit = 10
            elif data['subscription_type'] == 'enterprise':
                user.scan_quota_limit = 20
            else:
                user.scan_quota_limit = 0
    
    try:
        db.session.commit()
        current_app.logger.info(f"Admin {current_user.email} a mis à jour l'abonnement #{subscription_id}")
        return jsonify({'message': 'Abonnement mis à jour avec succès'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la mise à jour de l'abonnement: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/scans', methods=['GET'])
@login_required
@admin_required
def get_scans():
    """Récupère la liste des scans"""
    scans = ScanHistory.query.order_by(desc(ScanHistory.created_at)).all()
    result = []
    
    for scan in scans:
        user = User.query.get(scan.user_id)
        scan_data = {
            'id': scan.id,
            'user_id': scan.user_id,
            'user_name': f"{user.first_name} {user.last_name}" if user else "Utilisateur inconnu",
            'user_email': user.email if user else "Email inconnu",
            'target_ip': scan.target_ip,
            'scan_type': scan.scan_type,
            'status': scan.status,
            'score': scan.score,
            'created_at': scan.created_at.isoformat(),
            'completed_at': scan.completed_at.isoformat() if scan.completed_at else None
        }
        result.append(scan_data)
    
    return jsonify(result)

@admin_bp.route('/scans/<int:scan_id>', methods=['GET'])
@login_required
@admin_required
def get_scan(scan_id):
    """Récupère les détails d'un scan spécifique"""
    scan = ScanHistory.query.get_or_404(scan_id)
    user = User.query.get(scan.user_id)
    
    # Récupérer le rapport associé
    report = Report.query.filter_by(scan_id=scan_id).first()
    report_data = None
    
    if report:
        report_data = {
            'id': report.id,
            'content': json.loads(report.content) if report.content else {},
            'created_at': report.created_at.isoformat()
        }
    
    scan_data = {
        'id': scan.id,
        'user_id': scan.user_id,
        'user_name': f"{user.first_name} {user.last_name}" if user else "Utilisateur inconnu",
        'user_email': user.email if user else "Email inconnu",
        'target_ip': scan.target_ip,
        'scan_type': scan.scan_type,
        'status': scan.status,
        'score': scan.score,
        'created_at': scan.created_at.isoformat(),
        'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
        'report': report_data
    }
    
    return jsonify(scan_data)

@admin_bp.route('/dashboard/stats', methods=['GET'])
@login_required
@admin_required
def get_dashboard_stats():
    """Récupère les statistiques pour le tableau de bord admin"""
    # Nombre total d'utilisateurs
    total_users = User.query.count()
    
    # Nombre d'abonnements actifs
    active_subscriptions = User.query.filter(
        User.subscription_end_date >= datetime.utcnow(),
        User.offer_type.in_(['pro', 'enterprise'])
    ).count()
    
    # Nombre total de scans
    total_scans = ScanHistory.query.count()
    
    # Revenus estimés (somme des prix des abonnements actifs)
    revenue = db.session.query(db.func.sum(Subscription.price)).filter(
        Subscription.status == 'active'
    ).scalar() or 0
    
    # Distribution des offres
    free_users = User.query.filter_by(offer_type='free').count()
    pro_users = User.query.filter_by(offer_type='pro').count()
    enterprise_users = User.query.filter_by(offer_type='enterprise').count()
    
    # Évolution des abonnements sur l'année
    current_year = datetime.utcnow().year
    monthly_subscriptions = []
    
    for month in range(1, 13):
        start_date = datetime(current_year, month, 1)
        if month == 12:
            end_date = datetime(current_year + 1, 1, 1)
        else:
            end_date = datetime(current_year, month + 1, 1)
        
        pro_count = Subscription.query.filter(
            Subscription.created_at >= start_date,
            Subscription.created_at < end_date,
            Subscription.subscription_type == 'pro'
        ).count()
        
        enterprise_count = Subscription.query.filter(
            Subscription.created_at >= start_date,
            Subscription.created_at < end_date,
            Subscription.subscription_type == 'enterprise'
        ).count()
        
        monthly_subscriptions.append({
            'month': month,
            'pro': pro_count,
            'enterprise': enterprise_count
        })
    
    # Activité récente
    recent_activity = []
    
    # Nouveaux utilisateurs
    new_users = User.query.order_by(desc(User.created_at)).limit(5).all()
    for user in new_users:
        recent_activity.append({
            'type': 'new_user',
            'user_id': user.id,
            'user_name': f"{user.first_name} {user.last_name}",
            'user_email': user.email,
            'timestamp': user.created_at.isoformat()
        })
    
    # Nouveaux abonnements
    new_subscriptions = Subscription.query.order_by(desc(Subscription.created_at)).limit(5).all()
    for sub in new_subscriptions:
        user = User.query.get(sub.user_id)
        recent_activity.append({
            'type': 'new_subscription',
            'subscription_id': sub.id,
            'user_id': sub.user_id,
            'user_name': f"{user.first_name} {user.last_name}" if user else "Utilisateur inconnu",
            'subscription_type': sub.subscription_type,
            'timestamp': sub.created_at.isoformat()
        })
    
    # Scans récents
    recent_scans = ScanHistory.query.order_by(desc(ScanHistory.created_at)).limit(5).all()
    for scan in recent_scans:
        user = User.query.get(scan.user_id)
        recent_activity.append({
            'type': 'scan_completed',
            'scan_id': scan.id,
            'user_id': scan.user_id,
            'user_name': f"{user.first_name} {user.last_name}" if user else "Utilisateur inconnu",
            'target_ip': scan.target_ip,
            'score': scan.score,
            'timestamp': scan.completed_at.isoformat() if scan.completed_at else scan.created_at.isoformat()
        })
    
    # Trier l'activité récente par date
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = recent_activity[:10]  # Limiter à 10 éléments
    
    return jsonify({
        'total_users': total_users,
        'active_subscriptions': active_subscriptions,
        'total_scans': total_scans,
        'revenue': revenue,
        'offer_distribution': {
            'free': free_users,
            'pro': pro_users,
            'enterprise': enterprise_users
        },
        'monthly_subscriptions': monthly_subscriptions,
        'recent_activity': recent_activity
    })

@admin_bp.route('/settings', methods=['GET'])
@login_required
@admin_required
def get_settings():
    """Récupère les paramètres système"""
    # Ici, vous pourriez récupérer les paramètres depuis une table de configuration
    # Pour l'instant, on renvoie des valeurs par défaut
    
    return jsonify({
        'subscription_prices': {
            'pro': {
                'monthly': 40000,
                'quarterly': 108000,
                'yearly': 384000
            },
            'enterprise': {
                'monthly': 80000,
                'quarterly': 216000,
                'yearly': 768000
            }
        },
        'scan_quotas': {
            'pro': 10,
            'enterprise': 20
        },
        'system': {
            'maintenance_mode': False,
            'version': '1.0.0',
            'last_update': datetime.utcnow().isoformat()
        }
    })

@admin_bp.route('/settings', methods=['PUT'])
@login_required
@admin_required
def update_settings():
    """Met à jour les paramètres système"""
    data = request.get_json()
    
    # Ici, vous pourriez sauvegarder les paramètres dans une table de configuration
    # Pour l'instant, on simule juste la mise à jour
    
    current_app.logger.info(f"Admin {current_user.email} a mis à jour les paramètres système")
    return jsonify({'message': 'Paramètres mis à jour avec succès'})

# Routes pour servir les pages HTML de l'interface admin
@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return current_app.send_static_file('admin/dashboard.html')

@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    return current_app.send_static_file('admin/users.html')

@admin_bp.route('/users/<int:user_id>/edit')
@login_required
@admin_required
def admin_edit_user(user_id):
    return current_app.send_static_file('admin/user_edit.html')

@admin_bp.route('/subscriptions')
@login_required
@admin_required
def admin_subscriptions():
    return current_app.send_static_file('admin/subscriptions.html')

@admin_bp.route('/scans')
@login_required
@admin_required
def admin_scans():
    return current_app.send_static_file('admin/scans.html')

@admin_bp.route('/settings')
@login_required
@admin_required
def admin_settings():
    return current_app.send_static_file('admin/settings.html')

@admin_bp.route('/login')
def admin_login():
    return current_app.send_static_file('admin/login.html')
