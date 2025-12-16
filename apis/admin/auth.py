# apis/auth/auth.py

import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
import jwt
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer

from models.admin.admin import Admin
from models.lawyer.lawyer import Lawyer
from models.user.user import User
from config.db.session import SessionLocal

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set")

# -------------------------------
# Database dependency
# -------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------
# Password hashing
# -------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------------
# OAuth2 scheme
# -------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# -------------------------------
# Pydantic Schemas
# -------------------------------
class LoginInput(BaseModel):
    email: EmailStr
    password: str
    role: str  # admin | lawyer | user

    @validator("role")
    def validate_role(cls, v):
        allowed = {"admin", "lawyer", "user"}
        if v not in allowed:
            raise ValueError("Role must be admin, lawyer, or user")
        return v

    @validator("password")
    def password_strength(cls, v):
        if len(v.strip()) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    full_name: str | None
    email: EmailStr
    phone_number: str | None
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    user: UserResponse
    token: TokenData

# -------------------------------
# Auth Service
# -------------------------------
class AuthService:

    @staticmethod
    def authenticate(db: Session, email: str, password: str, role: str):
        """
        Authenticate user based on selected role
        """

        if role == "admin":
            admin = db.query(Admin).filter(Admin.email == email).first()
            if not admin or not pwd_context.verify(password, admin.hashed_password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
            return admin

        if role == "lawyer":
            lawyer = db.query(Lawyer).filter(Lawyer.email == email).first()
            if not lawyer or not pwd_context.verify(password, lawyer.password):
                raise HTTPException(status_code=401, detail="Invalid lawyer credentials")
            return lawyer

        if role == "user":
            user = db.query(User).filter(User.email == email).first()
            if not user or not pwd_context.verify(password, user.hashed_password):
                raise HTTPException(status_code=401, detail="Invalid user credentials")
            return user

        raise HTTPException(status_code=400, detail="Invalid role")

# -------------------------------
# JWT Helpers
# -------------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Decode JWT and fetch logged-in user
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id or not role:
            raise HTTPException(status_code=401, detail="Invalid token")

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if role == "admin":
        user = db.query(Admin).filter(Admin.id == user_id).first()
    elif role == "lawyer":
        user = db.query(Lawyer).filter(Lawyer.id == user_id).first()
    elif role == "user":
        user = db.query(User).filter(User.id == user_id).first()
    else:
        user = None

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user, role

# -------------------------------
# Router
# -------------------------------
auth_router = APIRouter(prefix="/auth", tags=["Auth"])

# -------------------------------
# Login Route
# -------------------------------
@auth_router.post("/login", response_model=LoginResponse)
def login(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Login with email + password + role
    """

    role = role.lower()

    user_obj = AuthService.authenticate(db, email, password, role)

    user_data = {
        "id": user_obj.id,
        "full_name": getattr(user_obj, "full_name", getattr(user_obj, "name", None)),
        "email": user_obj.email,
        "phone_number": getattr(user_obj, "phone_number", None),
        "role": role,
        "created_at": user_obj.created_at,
        "updated_at": user_obj.updated_at
    }

    token = create_access_token(
        {
            "sub": user_obj.id,
            "role": role
        }
    )

    return LoginResponse(
        user=UserResponse(**user_data),
        token=TokenData(access_token=token)
    )
