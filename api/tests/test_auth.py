# Fichier: api/tests/test_auth.py

import pytest
from api.models import User

def test_register_success(client, init_database):
    """Teste l'inscription réussie d'un nouvel utilisateur."""
    response = client.post("/api/auth/register", json={
        "firstName": "New",
        "lastName": "User",
        "email": "newuser@example.com",
        "password": "newpassword"
    })
    assert response.status_code == 200 # Ou 201 Created si vous préférez
    assert "message" in response.json
    assert response.json["message"] == "Inscription réussie"
    # Vérifier que l'utilisateur est bien créé en base
    user = User.query.filter_by(email="newuser@example.com").first()
    assert user is not None
    assert user.first_name == "New"

def test_register_duplicate_email(client, init_database):
    """Teste l'échec de l'inscription avec un email déjà existant."""
    # L'utilisateur test@example.com est créé dans init_database
    response = client.post("/api/auth/register", json={
        "firstName": "Another",
        "lastName": "User",
        "email": "test@example.com", # Email déjà utilisé
        "password": "anotherpassword"
    })
    assert response.status_code == 409
    assert "message" in response.json
    assert "déjà utilisé" in response.json["message"]

def test_register_missing_fields(client, init_database):
    """Teste l'échec de l'inscription avec des champs manquants."""
    response = client.post("/api/auth/register", json={
        "firstName": "Missing",
        "email": "missing@example.com",
        "password": "missingpassword"
        # lastName est manquant
    })
    assert response.status_code == 400
    assert "message" in response.json
    assert "manquant" in response.json["message"]

def test_login_success(client, init_database):
    """Teste la connexion réussie d'un utilisateur existant."""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password"
    })
    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == "Connexion réussie"
    # Vérifier que le cookie de session est bien positionné (si possible/pertinent)
    # assert 'session' in response.headers.get('Set-Cookie', '')

def test_login_wrong_password(client, init_database):
    """Teste l'échec de la connexion avec un mot de passe incorrect."""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "message" in response.json
    assert "invalides" in response.json["message"]

def test_login_unknown_user(client, init_database):
    """Teste l'échec de la connexion avec un utilisateur inconnu."""
    response = client.post("/api/auth/login", json={
        "email": "unknown@example.com",
        "password": "password"
    })
    assert response.status_code == 401
    assert "message" in response.json
    assert "invalides" in response.json["message"]

def test_logout_success(logged_in_client):
    """Teste la déconnexion réussie d'un utilisateur connecté."""
    response = logged_in_client.post("/api/auth/logout")
    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == "Déconnexion réussie"
    # Vérifier que l'utilisateur n'est plus connecté (ex: via /status)
    status_response = logged_in_client.get("/api/auth/status")
    assert status_response.status_code == 200 # La route status retourne 200 même si non loggué
    assert not status_response.json["loggedIn"]

def test_status_logged_in(logged_in_client):
    """Teste l'endpoint /status pour un utilisateur connecté."""
    response = logged_in_client.get("/api/auth/status")
    assert response.status_code == 200
    data = response.json
    assert data["loggedIn"] is True
    assert data["user"] is not None
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["firstName"] == "Test"

def test_status_logged_out(client, init_database):
    """Teste l'endpoint /status pour un utilisateur non connecté."""
    response = client.get("/api/auth/status")
    assert response.status_code == 200
    data = response.json
    assert data["loggedIn"] is False
    assert data["user"] is None

