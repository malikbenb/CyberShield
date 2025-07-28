# Fichier : api/auth.py

from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from models import db, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Configuration de Flask-Login
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    # Retourner une erreur 401 si l'utilisateur n'est pas authentifié et essaie d'accéder à une ressource protégée
    return jsonify({"message": "Authentification requise"}), 401

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    first_name = data.get("firstName")
    last_name = data.get("lastName")
    email = data.get("email")
    password = data.get("password")

    if not all([first_name, last_name, email, password]):
        return jsonify({"message": "Tous les champs sont requis"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Cet email est déjà utilisé"}), 409 # 409 Conflict

    new_user = User(first_name=first_name, last_name=last_name, email=email)
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        # Connecter l'utilisateur directement après l'inscription
        login_user(new_user)
        return jsonify({
            "message": "Inscription réussie",
            "user": {
                "id": new_user.id,
                "firstName": new_user.first_name,
                "lastName": new_user.last_name,
                "email": new_user.email
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'inscription: {e}") # Log pour le débogage
        return jsonify({"message": "Erreur lors de l'inscription"}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email et mot de passe requis"}), 400

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        login_user(user) # Gère la session utilisateur
        return jsonify({
            "message": "Connexion réussie",
            "user": {
                "id": user.id,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "email": user.email
            }
        }), 200
    else:
        return jsonify({"message": "Email ou mot de passe incorrect"}), 401

@auth_bp.route("/logout", methods=["POST"])
@login_required # S'assurer que l'utilisateur est connecté pour se déconnecter
def logout():
    logout_user() # Efface la session utilisateur
    return jsonify({"message": "Déconnexion réussie"}), 200

@auth_bp.route("/status", methods=["GET"])
@login_required
def status():
    # Route pour vérifier si l'utilisateur est actuellement connecté (utile pour le frontend)
    return jsonify({
        "loggedIn": True,
        "user": {
            "id": current_user.id,
            "firstName": current_user.first_name,
            "lastName": current_user.last_name,
            "email": current_user.email
        }
    }), 200

# Fonction pour initialiser l'authentification dans l'application Flask
def init_auth(app):
    # Clé secrète pour les sessions Flask (IMPORTANT: utiliser une vraie clé secrète en production)
    app.config['SECRET_KEY'] = 'dev_secret_key_replace_in_prod' 
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)

