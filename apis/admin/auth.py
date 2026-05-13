# apis/auth/auth.py

import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form, Body
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
from schemas.password_reset import ForgotPasswordRequest, ResetPasswordRequest, PasswordResetResponse

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
    request: LoginInput = Body(...),
    db: Session = Depends(get_db)
):
    """
    Login with email + password + role (JSON body)
    """
    import json
    print(f"\n🔍 DEBUG LOGIN - Request received: email={request.email}, password_len={len(request.password)}, role={request.role}")
    
    role = request.role.lower()

    user_obj = AuthService.authenticate(db, request.email, request.password, role)

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


# ============================================================
# FORGOT PASSWORD - REQUEST RESET
# ============================================================
@auth_router.post("/forgot-password", response_model=PasswordResetResponse)
def forgot_password(
    request: ForgotPasswordRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Request password reset. Email will be sent with reset link.
    Supported roles: lawyer, user, admin
    """
    role = request.role.lower()

    if role == "lawyer":
        from service.lawyer.lawyer import LawyerService
        result = LawyerService.forgot_password(db, request.email)
        return PasswordResetResponse(success=True, message=result["message"])

    elif role == "user":
        from service.user.user import UserService
        result = UserService.forgot_password(db, request.email)
        return PasswordResetResponse(success=True, message=result["message"])

    elif role == "admin":
        from service.admin.admin import AdminService
        result = AdminService.forgot_password(db, request.email)
        return PasswordResetResponse(success=True, message=result["message"])

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be: lawyer, user, or admin"
        )


# ============================================================
# RESET PASSWORD - WITH TOKEN
# ============================================================
@auth_router.post("/reset-password", response_model=PasswordResetResponse)
def reset_password(
    request: ResetPasswordRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token.
    Token is obtained from forgot password email.
    """
    try:
        # Decode token to determine user type
        payload = jwt.decode(request.token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_type = payload.get("type")

        if user_type == "lawyer":
            from service.lawyer.lawyer import LawyerService
            result = LawyerService.reset_password(db, request.token, request.new_password)
            return PasswordResetResponse(success=True, message=result["message"])

        elif user_type == "user":
            from service.user.user import UserService
            result = UserService.reset_password(db, request.token, request.new_password)
            return PasswordResetResponse(success=True, message=result["message"])

        elif user_type == "admin":
            from service.admin.admin import AdminService
            result = AdminService.reset_password(db, request.token, request.new_password)
            return PasswordResetResponse(success=True, message=result["message"])

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
