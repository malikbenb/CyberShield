import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from api.main import app
from api.models import User, Subscription, SubscriptionPlan, SubscriptionDuration
from api.auth import create_access_token

client = TestClient(app)

def test_user_creation():
    """Test la création d'un utilisateur."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User"
    )
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active == True
    assert user.is_admin == False

def test_subscription_creation():
    """Test la création d'un abonnement."""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    subscription = Subscription(
        user_id=1,
        plan=SubscriptionPlan.PRO,
        duration=SubscriptionDuration.MONTHLY,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    
    assert subscription.user_id == 1
    assert subscription.plan == SubscriptionPlan.PRO
    assert subscription.duration == SubscriptionDuration.MONTHLY
    assert subscription.start_date == start_date
    assert subscription.end_date == end_date
    assert subscription.is_active == True

def test_subscription_is_valid():
    """Test la méthode is_valid de l'abonnement."""
    # Abonnement actif et non expiré
    start_date = datetime.now() - timedelta(days=10)
    end_date = datetime.now() + timedelta(days=20)
    
    subscription = Subscription(
        user_id=1,
        plan=SubscriptionPlan.PRO,
        duration=SubscriptionDuration.MONTHLY,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    
    assert subscription.is_valid() == True
    
    # Abonnement expiré
    start_date = datetime.now() - timedelta(days=40)
    end_date = datetime.now() - timedelta(days=10)
    
    subscription = Subscription(
        user_id=1,
        plan=SubscriptionPlan.PRO,
        duration=SubscriptionDuration.MONTHLY,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    
    assert subscription.is_valid() == False
    
    # Abonnement inactif
    start_date = datetime.now() - timedelta(days=10)
    end_date = datetime.now() + timedelta(days=20)
    
    subscription = Subscription(
        user_id=1,
        plan=SubscriptionPlan.PRO,
        duration=SubscriptionDuration.MONTHLY,
        start_date=start_date,
        end_date=end_date,
        is_active=False
    )
    
    assert subscription.is_valid() == False
