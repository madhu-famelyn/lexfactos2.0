from sqlalchemy.orm import Session
from models.admin.admin import Admin
from schemas.admin.admin import AdminCreate, AdminUpdate
from passlib.context import CryptContext
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import uuid
import re
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AdminService:

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def validate_full_name(full_name: str):
        if not full_name.strip():
            raise ValueError("Full name must not be empty")
        if len(full_name) < 2 or len(full_name) > 100:
            raise ValueError("Full name must be between 2 and 100 characters")

    @staticmethod
    def validate_email(email: str):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise ValueError("Invalid email format. Must be like user@example.com")

    @staticmethod
    def validate_mobile(mobile_number: str):
        pattern = r"^\d{10,15}$"
        if not re.match(pattern, mobile_number):
            raise ValueError("Mobile number atleast 10 digits")

    @staticmethod
    def validate_password(password: str):
        if not password.strip():
            raise ValueError("Password cannot be empty")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")

    @staticmethod
    def create_admin(db: Session, data: AdminCreate) -> Admin:
        # Validate fields
        AdminService.validate_full_name(data.full_name)
        AdminService.validate_email(data.email)
        AdminService.validate_mobile(data.mobile_number)
        AdminService.validate_password(data.password)

        # Check existing email
        if db.query(Admin).filter(Admin.email == data.email).first():
            raise ValueError("Admin with this email already exists")

        # Check existing mobile
        if db.query(Admin).filter(Admin.mobile_number == data.mobile_number).first():
            raise ValueError("Admin with this mobile number already exists")

        admin = Admin(
            id=str(uuid.uuid4()),
            full_name=data.full_name,
            email=data.email,
            mobile_number=data.mobile_number,
            hashed_password=AdminService.hash_password(data.password)
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    @staticmethod
    def get_admin_by_id(db: Session, admin_id: str) -> Admin:
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise ValueError("Admin not found")
        return admin

    @staticmethod
    def get_admin_by_email(db: Session, email: str) -> Admin | None:
        return db.query(Admin).filter(Admin.email == email).first()

    @staticmethod
    def get_all_admins(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Admin).offset(skip).limit(limit).all()

    @staticmethod
    def update_admin(db: Session, admin: Admin, updates: AdminUpdate) -> Admin:
        update_data = updates.dict(exclude_unset=True)

        if "full_name" in update_data:
            AdminService.validate_full_name(update_data["full_name"])
        if "email" in update_data:
            AdminService.validate_email(update_data["email"])
            # Check duplicate email
            existing = db.query(Admin).filter(Admin.email == update_data["email"], Admin.id != admin.id).first()
            if existing:
                raise ValueError("Another admin with this email already exists")
        if "mobile_number" in update_data:
            AdminService.validate_mobile(update_data["mobile_number"])
            # Check duplicate mobile
            existing = db.query(Admin).filter(Admin.mobile_number == update_data["mobile_number"], Admin.id != admin.id).first()
            if existing:
                raise ValueError("Another admin with this mobile number already exists")
        if "password" in update_data:
            AdminService.validate_password(update_data["password"])
            update_data["hashed_password"] = AdminService.hash_password(update_data.pop("password"))

        for key, value in update_data.items():
            setattr(admin, key, value)

        db.commit()
        db.refresh(admin)
        return admin

    @staticmethod
    def delete_admin(db: Session, admin: Admin) -> None:
        if not admin:
            raise ValueError("Admin not found")
        db.delete(admin)
        db.commit()

    # ============================================================
    # PASSWORD RESET - FORGOT PASSWORD
    # ============================================================
    @staticmethod
    def forgot_password(db: Session, email: str) -> dict:
        """
        Generate password reset token and send email for admin
        """
        admin = db.query(Admin).filter(Admin.email == email).first()
        
        if not admin:
            # Don't reveal if email exists (security best practice)
            return {"message": "If email exists, password reset link has been sent"}

        # Generate reset token (valid for 30 minutes)
        reset_data = {
            "sub": admin.id,
            "type": "admin",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        reset_token = jwt.encode(reset_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Send email
        from utiles.email_service import EmailService
        email_sent = EmailService.send_password_reset_email(
            recipient_email=admin.email,
            recipient_name=admin.full_name,
            reset_token=reset_token,
            user_type="admin"
        )

        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email"
            )

        return {"message": "If email exists, password reset link has been sent"}

    @staticmethod
    def verify_reset_token(token: str) -> dict:
        """
        Verify password reset token and extract admin info
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            if payload.get("type") != "admin":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
            
            return {"id": payload.get("sub"), "type": payload.get("type")}
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> dict:
        """
        Reset admin password with valid token
        """
        # Verify token
        token_data = AdminService.verify_reset_token(token)
        admin_id = token_data["id"]

        # Get admin
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        # Update password
        AdminService.validate_password(new_password)
        admin.hashed_password = AdminService.hash_password(new_password)
        db.commit()
        db.refresh(admin)

        return {"message": "Password reset successfully"}
