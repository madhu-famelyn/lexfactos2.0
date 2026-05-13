from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv

from models.user.user import User
from schemas.user.user import UserCreate, UserUpdate

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# -------------------------------------------------
# Password hashing (kept here intentionally)
# -------------------------------------------------

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


# -------------------------------------------------
# User Service
# -------------------------------------------------

class UserService:
    """
    All user-related business logic lives here.
    Routers should NOT contain DB logic.
    """

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        # ---- check email uniqueness ----
        if db.query(User).filter(User.email == user_in.email).first():
            raise ValueError("Email already registered")

        # ---- check phone uniqueness ----
        if (
            db.query(User)
            .filter(User.phone_number == user_in.phone_number)
            .first()
        ):
            raise ValueError("Phone number already registered")

        # ---- create user ----
        user = User(
            name=user_in.name,
            email=user_in.email,
            phone_number=user_in.phone_number,
            hashed_password=hash_password(user_in.password),
        )

        db.add(user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Failed to create user")

        db.refresh(user)
        return user

    @staticmethod
    def update_user(
        db: Session,
        user: User,
        user_in: UserUpdate
    ) -> User:
        if user_in.name is not None:
            user.name = user_in.name

        if user_in.phone_number is not None:
            user.phone_number = user_in.phone_number

        if user_in.password is not None:
            user.hashed_password = hash_password(user_in.password)

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    # ============================================================
    # PASSWORD RESET - FORGOT PASSWORD
    # ============================================================
    @staticmethod
    def forgot_password(db: Session, email: str) -> dict:
        """
        Generate password reset token and send email for user
        """
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Don't reveal if email exists (security best practice)
            return {"message": "If email exists, password reset link has been sent"}

        # Generate reset token (valid for 30 minutes)
        reset_data = {
            "sub": user.id,
            "type": "user",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        reset_token = jwt.encode(reset_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Send email
        from utiles.email_service import EmailService
        email_sent = EmailService.send_password_reset_email(
            recipient_email=user.email,
            recipient_name=user.name,
            reset_token=reset_token,
            user_type="user"
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
        Verify password reset token and extract user info
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            if payload.get("type") != "user":
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
        Reset user password with valid token
        """
        # Verify token
        token_data = UserService.verify_reset_token(token)
        user_id = token_data["id"]

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update password
        user.hashed_password = hash_password(new_password)
        db.commit()
        db.refresh(user)

        return {"message": "Password reset successfully"}
