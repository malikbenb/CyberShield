# Fichier: api/tests/conftest.py

import pytest
import os
from api.main import app as flask_app # Importer l'instance Flask de votre application
from api.models import db, User
from werkzeug.security import generate_password_hash

@pytest.fixture(scope="session")
def app():
    """Fixture pour créer une instance de l'application Flask pour les tests."""
    # Configurer l'application pour les tests
    flask_app.config.update({
        "TESTING": True,
        # Utiliser une base de données en mémoire pour les tests
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", 
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False, # Désactiver CSRF pour les tests de formulaires (si applicable)
        "LOGIN_DISABLED": False, # Garder l'authentification activée pour les tests
        # Autres configurations spécifiques aux tests...
    })

    # Créer les tables de la base de données
    with flask_app.app_context():
        db.create_all()

    yield flask_app

    # Nettoyer après les tests (si nécessaire, mais :memory: est généralement suffisant)
    # with flask_app.app_context():
    #     db.drop_all()

@pytest.fixture()
def client(app):
    """Fixture pour obtenir un client de test Flask."""
    return app.test_client()

@pytest.fixture()
def runner(app):
    """Fixture pour obtenir un lanceur de commandes CLI Flask (si nécessaire)."""
    return app.test_cli_runner()

@pytest.fixture(scope="function")
def init_database(app):
    """Fixture pour initialiser la base de données avant chaque test et la nettoyer après."""
    with app.app_context():
        db.create_all() # S'assurer que les tables existent
        
        # Optionnel: Ajouter des données initiales communes ici si nécessaire
        # Exemple: Créer un utilisateur de test
        test_user = User(
            email="test@example.com", 
            first_name="Test", 
            last_name="User",
            password_hash=generate_password_hash("password", method='pbkdf2:sha256')
        )
        db.session.add(test_user)
        db.session.commit()

        yield db # Fournir l'instance db aux tests si besoin

        db.session.remove() # Nettoyer la session
        db.drop_all() # Supprimer toutes les tables
        db.create_all() # Recréer les tables pour le prochain test

@pytest.fixture
def logged_in_client(client, init_database, app):
    """Fixture pour obtenir un client de test déjà connecté."""
    # Se connecter en utilisant le client de test
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password"
    })
    assert response.status_code == 200 # Vérifier que la connexion a réussi
    return client # Retourner le client maintenant connecté

