# Fichier: api/tests/test_dashboard_routes.py

import pytest
from unittest.mock import patch, MagicMock
from api.models import db, User, ScanHistory, Report
from datetime import datetime

# Test des routes GET (history, report, profile GET)

def test_get_scan_history_empty(logged_in_client):
    """Teste la récupération de l'historique quand il est vide."""
    response = logged_in_client.get("/api/dashboard/history")
    assert response.status_code == 200
    assert response.json == []

def test_get_scan_history_with_data(logged_in_client, init_database, app):
    """Teste la récupération de l'historique avec des données."""
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        scan1 = ScanHistory(user_id=user.id, target_ip="192.168.1.1", status="completed", scan_start_time=datetime.utcnow(), vulnerability_score=50)
        scan2 = ScanHistory(user_id=user.id, target_ip="192.168.1.2", status="running", scan_start_time=datetime.utcnow())
        db.session.add_all([scan1, scan2])
        db.session.commit()
        scan1_id = scan1.id # Get ID after commit
        # Add a report for scan1
        report1 = Report(scan_id=scan1_id, content='{"details": "..."}', format='json')
        db.session.add(report1)
        db.session.commit()

    response = logged_in_client.get("/api/dashboard/history")
    assert response.status_code == 200
    history = response.json
    assert len(history) == 2
    # Check structure of the first item (most recent, likely scan2)
    assert history[0]["target_ip"] == "192.168.1.2"
    assert history[0]["status"] == "running"
    assert history[0]["report_available"] is False
    assert history[1]["target_ip"] == "192.168.1.1"
    assert history[1]["status"] == "completed"
    assert history[1]["score"] == 50
    assert history[1]["report_available"] is True

def test_get_report_success(logged_in_client, init_database, app):
    """Teste la récupération réussie d'un rapport existant."""
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        scan = ScanHistory(user_id=user.id, target_ip="192.168.1.3", status="completed")
        db.session.add(scan)
        db.session.commit()
        scan_id = scan.id
        report = Report(scan_id=scan_id, content='{"vulnerabilities": []}', format='json')
        db.session.add(report)
        db.session.commit()

    response = logged_in_client.get(f"/api/dashboard/report/{scan_id}")
    assert response.status_code == 200
    report_data = response.json
    assert report_data["scan_id"] == scan_id
    assert report_data["format"] == "json"
    assert report_data["content"] == '{"vulnerabilities": []}'

def test_get_report_not_found(logged_in_client):
    """Teste la récupération d'un rapport pour un scan inexistant."""
    response = logged_in_client.get("/api/dashboard/report/999")
    assert response.status_code == 404

def test_get_report_no_report_available(logged_in_client, init_database, app):
    """Teste la récupération d'un rapport quand le scan existe mais pas le rapport."""
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        scan = ScanHistory(user_id=user.id, target_ip="192.168.1.4", status="running")
        db.session.add(scan)
        db.session.commit()
        scan_id = scan.id

    response = logged_in_client.get(f"/api/dashboard/report/{scan_id}")
    assert response.status_code == 404 # Report not found
    assert "Rapport non disponible" in response.json["message"]

def test_get_profile(logged_in_client):
    """Teste la récupération du profil utilisateur."""
    response = logged_in_client.get("/api/dashboard/profile")
    assert response.status_code == 200
    profile = response.json
    assert profile["email"] == "test@example.com"
    assert profile["firstName"] == "Test"
    assert profile["lastName"] == "User"

# Test de la route PUT /profile

def test_update_profile_info_success(logged_in_client, app):
    """Teste la mise à jour réussie des informations du profil."""
    response = logged_in_client.put("/api/dashboard/profile", json={
        "firstName": "Updated",
        "lastName": "Name"
    })
    assert response.status_code == 200
    assert "Profil mis à jour" in response.json["message"]
    # Vérifier en base
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user.first_name == "Updated"
        assert user.last_name == "Name"

def test_update_profile_password_success(logged_in_client, app):
    """Teste la mise à jour réussie du mot de passe."""
    response = logged_in_client.put("/api/dashboard/profile", json={
        "password": "newsecurepassword"
    })
    assert response.status_code == 200
    assert "Profil mis à jour" in response.json["message"]
    # Vérifier que l'ancien mot de passe ne fonctionne plus
    logout_resp = logged_in_client.post("/api/auth/logout")
    assert logout_resp.status_code == 200
    login_resp_old = logged_in_client.post("/api/auth/login", json={"email": "test@example.com", "password": "password"})
    assert login_resp_old.status_code == 401
    # Vérifier que le nouveau mot de passe fonctionne
    login_resp_new = logged_in_client.post("/api/auth/login", json={"email": "test@example.com", "password": "newsecurepassword"})
    assert login_resp_new.status_code == 200

def test_update_profile_email_conflict(logged_in_client, init_database, app):
    """Teste l'échec de la mise à jour de l'email s'il est déjà pris."""
    with app.app_context(): # Créer un autre utilisateur
        other_user = User(email="other@example.com", first_name="Other", last_name="User", password_hash=generate_password_hash("password"))
        db.session.add(other_user)
        db.session.commit()
    
    response = logged_in_client.put("/api/dashboard/profile", json={
        "email": "other@example.com" # Email déjà utilisé
    })
    assert response.status_code == 409
    assert "déjà utilisé" in response.json["message"]

def test_update_profile_no_change(logged_in_client):
    """Teste la mise à jour du profil sans fournir de nouvelles données."""
    response = logged_in_client.put("/api/dashboard/profile", json={})
    assert response.status_code == 200 # Ou 400 si on veut forcer des données?
    assert "Aucune modification" in response.json["message"]

# Test de la route POST /scan/start

@patch("api.dashboard_routes.run_scan.delay") # Mocker la fonction delay de la tâche Celery
def test_start_scan_success(mock_run_scan_delay, logged_in_client, app):
    """Teste le démarrage réussi d'un scan Pro."""
    # Configurer le mock pour retourner un objet avec un id (simulant l'ID de tâche Celery)
    mock_task_result = MagicMock()
    mock_task_result.id = "mock_task_id_123"
    mock_run_scan_delay.return_value = mock_task_result

    target_ip = "198.51.100.1" # Exemple d'IP publique valide
    response = logged_in_client.post("/api/dashboard/scan/start", json={
        "target_ip": target_ip
    })

    assert response.status_code == 202
    data = response.json
    assert "Scan démarré" in data["message"]
    assert "scan_id" in data
    assert data["task_id"] == "mock_task_id_123"
    scan_id = data["scan_id"]

    # Vérifier que la tâche Celery a été appelée avec les bons arguments
    mock_run_scan_delay.assert_called_once_with(scan_id, target_ip)

    # Vérifier qu'un enregistrement ScanHistory a été créé en base
    with app.app_context():
        scan_history = ScanHistory.query.get(scan_id)
        assert scan_history is not None
        assert scan_history.target_ip == target_ip
        assert scan_history.status == "queued"
        user = User.query.filter_by(email="test@example.com").first()
        assert scan_history.user_id == user.id

@patch("api.dashboard_routes.run_scan.delay")
def test_start_scan_invalid_ip(mock_run_scan_delay, logged_in_client):
    """Teste l'échec du démarrage d'un scan avec une IP invalide."""
    response = logged_in_client.post("/api/dashboard/scan/start", json={
        "target_ip": "invalid-ip-address"
    })
    assert response.status_code == 400
    assert "Format d'adresse IP invalide" in response.json["message"]
    mock_run_scan_delay.assert_not_called() # Vérifier que la tâche n'a pas été appelée

@patch("api.dashboard_routes.run_scan.delay")
def test_start_scan_missing_ip(mock_run_scan_delay, logged_in_client):
    """Teste l'échec du démarrage d'un scan sans fournir d'IP."""
    response = logged_in_client.post("/api/dashboard/scan/start", json={})
    assert response.status_code == 400
    assert "Adresse IP cible manquante" in response.json["message"]
    mock_run_scan_delay.assert_not_called()

# Test d'accès non authentifié aux routes du dashboard

def test_dashboard_routes_unauthenticated(client, init_database):
    """Teste que les routes du dashboard nécessitent une authentification."""
    routes_to_test = [
        "/api/dashboard/history",
        "/api/dashboard/report/1",
        "/api/dashboard/profile",
        "/api/dashboard/scan/start"
    ]
    methods = {
        "/api/dashboard/history": "get",
        "/api/dashboard/report/1": "get",
        "/api/dashboard/profile": "get",
        "/api/dashboard/scan/start": "post"
    }
    
    for route in routes_to_test:
        method = getattr(client, methods[route])
        if methods[route] == 'post':
            response = method(route, json={}) # Envoyer un JSON vide pour POST
        else:
            response = method(route)
        # Flask-Login redirige vers la page de login par défaut (302) ou retourne 401 si configuré
        # Ici, comme on teste l'API, on s'attend à 401 (Unauthorized)
        assert response.status_code == 401, f"Route {route} did not return 401 Unauthorized"


