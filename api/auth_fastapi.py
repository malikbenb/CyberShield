# Fichier : api/auth_fastapi.py
# Version FastAPI avec authentification JWT (OAuth2)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session # Pour l'interaction synchrone avec la DB
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from typing import Optional

# Importer les modèles SQLAlchemy et la fonction pour obtenir la session DB
from models_fastapi import User
from database import get_db

# --- Configuration JWT ---
# !!! IMPORTANT : Utiliser une clé secrète forte et la gérer via des variables d'environnement en production !!!
SECRET_KEY = "votre_super_cle_secrete_ici_a_changer"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Durée de validité du token

# --- Configuration Hachage Mot de Passe ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Schéma OAuth2 ---
# tokenUrl pointe vers l'endpoint qui fournira le token (/auth/token dans ce cas)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# --- Modèles Pydantic ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    # Ajoutez d'autres champs si nécessaire, mais évitez le mot de passe
    class Config:
        orm_mode = True # Permet de créer le modèle depuis un objet SQLAlchemy

# --- Fonctions Utilitaires ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15) # Défaut 15 min
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dépendance pour obtenir l'utilisateur actuel ---
def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub") # "sub" est le sujet standard pour l'identifiant
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# --- Router FastAPI ---
auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentification"], # Tag pour la documentation Swagger
    responses={404: {"description": "Non trouvé"}},
)

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")
    
    hashed_password = get_password_hash(user.password)
    # Crée l'objet User SQLAlchemy
    db_user = User(
        email=user.email, 
        first_name=user.first_name, 
        last_name=user.last_name, 
        hashed_password=hashed_password # Assurez-vous que votre modèle User a un champ hashed_password
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        # Loggez l'erreur e pour le débogage
        print(f"Erreur DB lors de l'inscription: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création de l'utilisateur")

@auth_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, email=form_data.username) # OAuth2 utilise 'username' pour l'email/login
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    # Cette route est protégée, elle nécessite un token valide
    # current_user contient l'objet User SQLAlchemy récupéré depuis le token
    return current_user

# La route /logout n'est généralement pas nécessaire avec JWT stateless.
# La déconnexion se fait côté client en supprimant le token.
