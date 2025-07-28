# Fichier: api/errors.py

from flask import jsonify
from werkzeug.exceptions import HTTPException

# Dictionnaire pour personnaliser les messages d'erreur HTTP courants
error_messages = {
    400: "Requête incorrecte. Vérifiez les données envoyées.",
    401: "Authentification requise. Veuillez vous connecter.",
    403: "Accès interdit. Vous n'avez pas les permissions nécessaires.",
    404: "La ressource demandée n'a pas été trouvée.",
    405: "Méthode non autorisée pour cette ressource.",
    409: "Conflit. La ressource existe déjà ou une condition préalable n'est pas remplie.",
    429: "Trop de requêtes. Veuillez ralentir.",
    500: "Erreur interne du serveur. Veuillez réessayer plus tard.",
    503: "Service indisponible. Veuillez réessayer plus tard."
}

def handle_http_exception(e):
    """Gestionnaire global pour les exceptions HTTP Werkzeug."""
    # Utiliser le message personnalisé s'il existe, sinon le message par défaut de l'exception
    message = error_messages.get(e.code, e.description)
    response = jsonify(message=message, error_code=e.code)
    response.status_code = e.code
    # Logguer l'erreur ici si nécessaire, surtout pour les 5xx
    if e.code >= 500:
        print(f"Server Error ({e.code}): {e.original_exception if hasattr(e, 'original_exception') else e}")
    return response

def handle_generic_exception(e):
    """Gestionnaire pour les exceptions non prévues (erreurs 500)."""
    # Logguer l'exception complète pour le débogage
    print(f"Unhandled Exception: {e}")
    # Ne pas exposer les détails de l'erreur interne à l'utilisateur
    response = jsonify(message=error_messages[500], error_code=500)
    response.status_code = 500
    return response

def init_error_handlers(app):
    """Enregistre les gestionnaires d'erreurs sur l'application Flask."""
    # Enregistrer le gestionnaire pour toutes les exceptions HTTP
    for code in error_messages:
        app.register_error_handler(code, handle_http_exception)
    
    # Enregistrer un gestionnaire pour les exceptions génériques (celles qui ne sont pas des HTTPException)
    # Note: Ceci peut attraper des erreurs plus larges, à utiliser avec précaution.
    # Il est souvent préférable de laisser les erreurs 500 spécifiques être gérées par le framework
    # ou par le gestionnaire HTTPException si elles héritent de celle-ci.
    # app.register_error_handler(Exception, handle_generic_exception)
    
    # S'assurer que les erreurs 500 par défaut sont aussi gérées
    if 500 not in error_messages:
        app.register_error_handler(500, handle_http_exception)

    print("Gestionnaires d'erreurs initialisés.")


