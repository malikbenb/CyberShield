from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List
from datetime import datetime, timedelta
import json
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from auth_fastapi import get_current_user
from models_fastapi import User, Subscription, SubscriptionPlan
from database import get_db

# Modèles de données pour les paiements
class PaymentRequest(BaseModel):
    plan: str
    duration: int
    amount: float
    currency: str
    email: str
    name: str
    card_number: str
    expiry_date: str
    cvv: str
    address: str
    city: str
    postal_code: str
    
    @validator('plan')
    def validate_plan(cls, v):
        if v not in ['pro', 'enterprise']:
            raise ValueError('Le plan doit être "pro" ou "enterprise"')
        return v
    
    @validator('duration')
    def validate_duration(cls, v):
        if v not in [1, 3, 12]:
            raise ValueError('La durée doit être 1, 3 ou 12 mois')
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Le montant doit être positif')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v or '.' not in v:
            raise ValueError('Email invalide')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Le nom doit contenir au moins 2 caractères')
        return v.strip()
    
    @validator('card_number')
    def validate_card_number(cls, v):
        card_clean = v.replace(' ', '').replace('-', '')
        if not card_clean.isdigit() or len(card_clean) != 16:
            raise ValueError('Le numéro de carte doit contenir 16 chiffres')
        return card_clean
    
    @validator('expiry_date')
    def validate_expiry_date(cls, v):
        if '/' not in v or len(v) != 5:
            raise ValueError('La date d\'expiration doit être au format MM/AA')
        try:
            month, year = v.split('/')
            exp_month = int(month)
            exp_year = int('20' + year)
            
            if exp_month < 1 or exp_month > 12:
                raise ValueError('Mois invalide')
            
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            if exp_year < current_year or (exp_year == current_year and exp_month < current_month):
                raise ValueError('Carte expirée')
        except ValueError as e:
            if 'invalid literal' in str(e):
                raise ValueError('Format de date invalide')
            raise e
        return v
    
    @validator('cvv')
    def validate_cvv(cls, v):
        if not v.isdigit() or len(v) not in [3, 4]:
            raise ValueError('Le CVV doit contenir 3 ou 4 chiffres')
        return v
    
    @validator('address')
    def validate_address(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('L\'adresse doit contenir au moins 5 caractères')
        return v.strip()
    
    @validator('city')
    def validate_city(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('La ville doit contenir au moins 2 caractères')
        return v.strip()
    
    @validator('postal_code')
    def validate_postal_code(cls, v):
        if len(v.strip()) < 4:
            raise ValueError('Le code postal doit contenir au moins 4 caractères')
        return v.strip()

class PaymentResponse(BaseModel):
    success: bool
    message: str
    order_id: Optional[str] = None
    subscription_id: Optional[str] = None
    status: Optional[str] = None
    error_code: Optional[str] = None

# Router pour les paiements
payment_router = APIRouter(prefix="/api/payments", tags=["payments"])

# Simulation de base de données pour les paiements
payment_db = []

@payment_router.post("/process", response_model=PaymentResponse)
async def process_payment(payment: PaymentRequest, current_user: Optional[User] = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Traite un paiement simulé et crée un abonnement.
    Cette fonction simule l'intégration avec Stripe.
    """
    try:
        # Valider les informations de carte (simulation)
        if not validate_card(payment.card_number, payment.expiry_date, payment.cvv):
            return PaymentResponse(
                success=False,
                message="Informations de carte invalides",
                error_code="invalid_card"
            )
        
        # Générer un ID de commande
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        order_id = f"CS-{timestamp}"
        
        # Générer un ID d'abonnement
        subscription_id = f"sub_{timestamp}"
        
        # Déterminer le plan d'abonnement
        plan_name = payment.plan # "pro" ou "enterprise"
        
        # Déterminer la durée d'abonnement
        if payment.duration == 1:
            duration_str = "monthly"
        elif payment.duration == 3:
            duration_str = "quarterly"
        else:
            duration_str = "yearly"
        
        # Calculer les dates de début et de fin
        start_date = datetime.now()
        if payment.duration == 1:
            end_date = start_date + timedelta(days=30)
        elif payment.duration == 3:
            end_date = start_date + timedelta(days=90)
        else:
            end_date = start_date + timedelta(days=365)
        
        # Créer un nouvel abonnement
        new_subscription = {
            "id": subscription_id,
            "user_id": current_user.id if current_user else None,
            "email": payment.email,
            "name": payment.name,
            "plan": plan_name,
            "duration": duration_str,
            "amount": payment.amount,
            "currency": payment.currency,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status": "active",
            "order_id": order_id,
            "created_at": datetime.now().isoformat()
        }
        
        # Enregistrer le paiement
        payment_record = {
            "order_id": order_id,
            "subscription_id": subscription_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "email": payment.email,
            "name": payment.name,
            "card_last4": payment.card_number[-4:],
            "status": "succeeded",
            "created_at": datetime.now().isoformat()
        }
        
        # Ajouter à notre "base de données" simulée
        payment_db.append(payment_record)
        
        # Si l'utilisateur est connecté, mettre à jour son abonnement dans la base de données
        if current_user:
            try:
                # Mettre à jour l'utilisateur avec les nouvelles informations d'abonnement
                current_user.offer_type = plan_name  # "pro" ou "enterprise" selon le plan
                current_user.subscription_start_date = start_date
                current_user.subscription_end_date = end_date
                
                # Mettre à jour les quotas selon le type d'offre
                if plan_name == "pro":
                    current_user.scan_quota_limit = 10
                elif plan_name == "enterprise":
                    current_user.scan_quota_limit = 20
                
                # Réinitialiser le quota utilisé
                current_user.scan_quota_used = 0
                current_user.quota_period_start = start_date
                
                # Enregistrer les modifications dans la base de données
                db.commit()
                
                print(f"Abonnement mis à jour pour l'utilisateur {current_user.id}: {plan_name} jusqu'au {end_date}")
                
                # Créer une entrée dans la table Subscription si nécessaire
                # Cette partie est optionnelle si vous utilisez déjà les champs dans User
                try:
                    # Trouver le plan d'abonnement correspondant
                    subscription_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == plan_name).first()
                    
                    if not subscription_plan:
                        # Créer un plan par défaut si aucun n'existe
                        subscription_plan = SubscriptionPlan(
                            name=plan_name,
                            price_monthly=payment.amount if payment.duration == 1 else None,
                            price_annually=payment.amount if payment.duration == 12 else None,
                            scan_quota=current_user.scan_quota_limit,
                            description=f"Plan {plan_name} avec {current_user.scan_quota_limit} scans par mois",
                            is_active=True
                        )
                        db.add(subscription_plan)
                        db.flush()  # Pour obtenir l'ID du plan
                    
                    # Créer l'abonnement
                    subscription = Subscription(
                        user_id=current_user.id,
                        plan_id=subscription_plan.id,
                        subscription_type=plan_name,
                        start_date=start_date,
                        end_date=end_date,
                        price=payment.amount,
                        status="active",
                        notes=f"Abonnement {duration_str} créé via paiement {order_id}"
                    )
                    
                    db.add(subscription)
                    db.commit()
                    
                except Exception as sub_error:
                    print(f"Erreur lors de la création de l'entrée Subscription: {sub_error}")
                    # Ne pas échouer le paiement si cette partie échoue
                    # L'utilisateur a déjà son abonnement mis à jour dans la table User
                    db.rollback()
                
            except Exception as db_error:
                print(f"Erreur lors de la mise à jour de l'abonnement utilisateur: {db_error}")
                db.rollback()
                # Ne pas échouer le paiement si la mise à jour de la base échoue
                # Nous avons déjà simulé un paiement réussi
        
        return PaymentResponse(
            success=True,
            message="Paiement traité avec succès",
            order_id=order_id,
            subscription_id=subscription_id,
            status="active"
        )
        
    except Exception as e:
        # Log l'erreur pour le débogage
        print(f"Error processing payment: {e}") 
        return PaymentResponse(
            success=False,
            message=f"Erreur lors du traitement du paiement: {str(e)}",
            error_code="processing_error"
        )

def validate_card(card_number: str, expiry_date: str, cvv: str) -> bool:
    """
    Valide les informations de carte (simulation).
    Dans une implémentation réelle, cette fonction appellerait Stripe.
    """
    # Vérifier que le numéro de carte a 16 chiffres
    card_number = card_number.replace(" ", "")
    if not card_number.isdigit() or len(card_number) != 16:
        return False
    
    # Vérifier que la date d'expiration est au format MM/YY et n'est pas expirée
    try:
        month, year = expiry_date.split("/")
        exp_month = int(month)
        exp_year = int("20" + year)
        
        if exp_month < 1 or exp_month > 12:
            return False
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        if exp_year < current_year or (exp_year == current_year and exp_month < current_month):
            return False
    except:
        return False
    
    # Vérifier que le CVV a 3 ou 4 chiffres
    if not cvv.isdigit() or len(cvv) not in [3, 4]:
        return False
    
    # Simuler une validation réussie pour certains numéros de carte
    # Dans une implémentation réelle, cette logique serait remplacée par un appel à Stripe
    if card_number.startswith("4") or card_number.startswith("5"):
        return True
    
    return False

@payment_router.get("/verify/{order_id}", response_model=PaymentResponse)
async def verify_payment(order_id: str, current_user: Optional[User] = Depends(get_current_user)):
    """
    Vérifie le statut d'un paiement.
    """
    # Rechercher le paiement dans notre "base de données" simulée
    payment = next((p for p in payment_db if p["order_id"] == order_id), None)
    
    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Paiement non trouvé"
        )
    
    return PaymentResponse(
        success=True,
        message="Paiement trouvé",
        order_id=payment["order_id"],
        subscription_id=payment["subscription_id"],
        status=payment["status"]
    )

@payment_router.get("/history")
async def get_payment_history(current_user: User = Depends(get_current_user)):
    """
    Récupère l'historique des paiements de l'utilisateur connecté.
    """
    user_payments = [p for p in payment_db if p.get("email") == current_user.email]
    return {"payments": user_payments}

