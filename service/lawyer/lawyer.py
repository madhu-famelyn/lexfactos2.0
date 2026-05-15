from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from fastapi import HTTPException, status
from passlib.context import CryptContext
from models.lawyer.lawyer import Lawyer
from sqlalchemy import func, or_, cast, String
from schemas.lawyer.lawyer import (
    LawyerCreate,
    LawyerUpdate,
    LawyerStatusUpdate,
    LawyerExcelUpload
)
import uuid
import json
import math
from datetime import datetime, timezone, timedelta
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LawyerService:

    # ============================================================
    # PASSWORD HASH FUNCTION
    # ============================================================
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    # ============================================================
    # SAFELY CLEAN EXCEL VALUES (convert nan → "")
    # ============================================================
    @staticmethod
    def _safe(value):
        if value is None:
            return ""
        if isinstance(value, float) and math.isnan(value):
            return ""
        return value

    # ============================================================
    # FIELD VALIDATIONS
    # ============================================================
    @staticmethod
    def _validate_full_name(name: str):
        if not name or not name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name is required."
            )
        if len(name) < 2 or len(name) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name must be between 2 and 100 characters."
            )

    @staticmethod
    def _validate_email(email: str):
        if not email or "@" not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid email is required."
            )

    @staticmethod
    def _validate_status(status: str):
        allowed = ["pending", "approved", "rejected"]
        if status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Status must be one of {allowed}."
            )

    @staticmethod
    def _validate_rejected_reason(status: str, reason: str):
        if status == "rejected" and not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejected reason is required when status is rejected."
            )
        if status in ["pending", "approved"] and reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejected reason must be empty for pending/approved status."
            )

    # ============================================================
    # MANUAL CREATE LAWYER
    # ============================================================
    @staticmethod
    def create_lawyer(db: Session, lawyer_data: LawyerCreate, file=None) -> Lawyer:
        data = lawyer_data.dict()

        if file:
            from utiles.s3_service import upload_to_s3
            image_url = upload_to_s3(file)
            data["image_url"] = image_url

        LawyerService._validate_full_name(data["full_name"])
        LawyerService._validate_email(data["email"])

        if db.query(Lawyer).filter(Lawyer.email == data["email"]).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists."
            )

        if db.query(Lawyer).filter(Lawyer.phone_number == data["phone_number"]).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists."
            )

        data["password"] = LawyerService.hash_password(data["password"])

        data.update({
            "lawyer_id": str(uuid.uuid4()),
            "role": "lawyer",
            "status": "pending",
            "rejected_reason": None
        })

        obj = Lawyer(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)

        # Send "profile under review" email to the lawyer
        try:
            from utiles.email_service import EmailService
            EmailService.send_profile_under_review_email(
                recipient_email=obj.email,
                recipient_name=obj.full_name
            )
        except Exception as email_err:
            print(f"[Warning] Could not send profile review email: {email_err}")

        return obj

    # ============================================================
    # UPDATE LAWYER
    # ============================================================
    @staticmethod
    def update_lawyer(db: Session, id: str, update_data: LawyerUpdate) -> Lawyer:
        lawyer = db.query(Lawyer).filter(Lawyer.id == id).first()
        if not lawyer:
            raise ValueError("Lawyer not found.")

        update_dict = update_data.dict(exclude_unset=True)

        if "full_name" in update_dict:
            LawyerService._validate_full_name(update_dict["full_name"])

        if "email" in update_dict:
            LawyerService._validate_email(update_dict["email"])

        for key, value in update_dict.items():
            setattr(lawyer, key, value)

        db.commit()
        db.refresh(lawyer)
        return lawyer

    # ============================================================
    # UPDATE STATUS ONLY
    # ============================================================
    @staticmethod
    def update_lawyer_status(db: Session, id: str, status_data: LawyerStatusUpdate) -> Lawyer:
        lawyer = db.query(Lawyer).filter(Lawyer.id == id).first()
        if not lawyer:
            raise ValueError("Lawyer not found.")

        LawyerService._validate_status(status_data.status)
        LawyerService._validate_rejected_reason(
            status_data.status, status_data.rejected_reason
        )

        lawyer.status = status_data.status
        lawyer.rejected_reason = status_data.rejected_reason

        db.commit()
        db.refresh(lawyer)

        # Send email notification to the lawyer about their profile status
        if status_data.status in ("approved", "rejected"):
            try:
                from utiles.email_service import EmailService
                EmailService.send_profile_status_update_email(
                    recipient_email=lawyer.email,
                    recipient_name=lawyer.full_name,
                    status=status_data.status,
                    rejected_reason=status_data.rejected_reason
                )
            except Exception as email_err:
                print(f"[Warning] Could not send profile status email: {email_err}")

        return lawyer

    # ============================================================
    # DELETE LAWYER
    # ============================================================
    @staticmethod
    def delete_lawyer(db: Session, id: str) -> dict:
        lawyer = db.query(Lawyer).filter(Lawyer.id == id).first()
        if not lawyer:
            raise ValueError("Lawyer not found.")

        try:
            db.delete(lawyer)
            db.commit()
            return {"message": "Lawyer deleted successfully", "id": id}
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete lawyer"
            )

    # ============================================================
    # BULK DELETE LAWYERS BY STATUS (Admin Feature)
    # ============================================================
    @staticmethod
    def delete_lawyers_by_status(db: Session, lawyer_status: str) -> dict:
        """Delete all lawyers with a specific status"""
        LawyerService._validate_status(lawyer_status)
        
        try:
            # Count lawyers with the specified status
            count = db.query(Lawyer).filter(Lawyer.status == lawyer_status).count()
            
            if count == 0:
                raise ValueError(f"No lawyers found with status '{lawyer_status}'.")
            
            # Delete all matching lawyers in one query
            db.query(Lawyer).filter(Lawyer.status == lawyer_status).delete(synchronize_session=False)
            db.commit()
            
            return {
                "message": f"Successfully deleted {count} lawyer(s)",
                "status": lawyer_status,
                "deleted_count": count
            }
        except ValueError as e:
            raise e
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete lawyers"
            )

    # ============================================================
    # GET LAWYER BY ID
    # ============================================================
    @staticmethod
    def get_lawyer_by_id(db: Session, id: str) -> Lawyer:
        lawyer = db.query(Lawyer).filter(Lawyer.id == id).first()
        if not lawyer:
            raise ValueError("Lawyer not found.")
        return lawyer

    # ============================================================
    # GET ALL LAWYERS
    # ============================================================
    @staticmethod
    def get_all_lawyers(db: Session) -> List[Lawyer]:
        return db.query(Lawyer).all()

    # ============================================================
    # GET LAWYERS BY STATUS
    # ============================================================
    @staticmethod
    def get_lawyers_by_status(db: Session, status: str) -> List[Lawyer]:
        LawyerService._validate_status(status)
        return db.query(Lawyer).filter(Lawyer.status == status).all()

    # ============================================================
    # BULK CREATE FROM EXCEL
    # ============================================================
    FIXED_IMAGE_URL = "https://fliplyn-assets.s3.ap-south-1.amazonaws.com/lawyers/f377e72b-1414-49d2-be61-7f7d78376497.png"

    @staticmethod
    def bulk_create_lawyers(db: Session, lawyers: List[LawyerExcelUpload]):
        created_lawyers = []

        for data in lawyers:
            clean = {k: LawyerService._safe(v) for k, v in data.dict().items()}

            LawyerService._validate_full_name(clean["full_name"])
            LawyerService._validate_email(clean["email"])

            random_password = uuid.uuid4().hex[:10]
            hashed_password = LawyerService.hash_password(random_password)

            lawyer = Lawyer(
                full_name=clean["full_name"],
                address_line_1=clean["address_line_1"],
                city=clean["city"],
                state=clean["state"],
                country=clean["country"],
                zip_code=clean["zip_code"],
                email=clean["email"],
                phone_number=clean["phone_number"],
                website_link=clean.get("website_link") or None,
                linkedin_link=clean.get("linkedin_link") or None,
                # Use Excel-provided image_url if given, else fall back to default
                image_url=(clean.get("image_url").strip() if isinstance(clean.get("image_url"), str) else clean.get("image_url")) or LawyerService.FIXED_IMAGE_URL,
                bio=clean.get("bio") or None,
                practice_areas=clean.get("practice_areas") or None,
                courts=clean.get("courts") or None,
                known_languages=clean.get("known_languages") or None,
                experience=clean.get("experience") or None,
                role="lawyer",
                status="approved",
                rejected_reason=None,
                password=hashed_password,
                lawyer_id=str(uuid.uuid4()),
            )

            db.add(lawyer)
            created_lawyers.append(lawyer)

        db.commit()
        return created_lawyers

    # ============================================================
    # SEARCH LAWYERS (keyword + country + pagination)
    # ============================================================
    @staticmethod
    def search_lawyers_by_country(
        db: Session,
        country: str,
        keyword: str = None,
        start: int = 1,
        end: int = 10
    ) -> List[Lawyer]:

        if not country:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Country name is required."
            )

        country = country.strip().lower()

        query = db.query(Lawyer).filter(
            func.lower(Lawyer.country) == country
        )

        if keyword:
            keyword = keyword.strip().lower()
            like = f"%{keyword}%"

            query = query.filter(
                or_(
                    func.lower(Lawyer.full_name).like(like),
                    func.lower(Lawyer.city).like(like),
                    func.lower(Lawyer.state).like(like),
                    func.lower(cast(Lawyer.known_languages, String)).like(like),
                )
            )

        limit = end - start + 1
        offset = start - 1

        results = query.offset(offset).limit(limit).all()

        # Return empty list instead of 404 for better API experience
        return results if results else []

        return results

    # ============================================================
    # UPDATE LAWYER POSITION
    # ============================================================
    @staticmethod
    def update_lawyer_position(
        db: Session,
        lawyer_id: str,
        position_status: str,
        position_status_days: int | None
    ):
        lawyer = db.query(Lawyer).filter(Lawyer.id == lawyer_id).first()

        if not lawyer:
            raise HTTPException(status_code=404, detail="Lawyer not found")

        position_status = position_status.lower()

        lawyer.position_status = position_status
        lawyer.position_status_days = position_status_days

        if position_status_days and position_status_days > 0:
            lawyer.position_status_expiry = (
                datetime.now(timezone.utc) +
                timedelta(days=position_status_days)
            )
        else:
            lawyer.position_status = "none"
            lawyer.position_status_days = None
            lawyer.position_status_expiry = None

        db.commit()
        db.refresh(lawyer)
        return lawyer

    # ============================================================
    # PASSWORD RESET - FORGOT PASSWORD
    # ============================================================
    @staticmethod
    def forgot_password(db: Session, email: str) -> dict:
        """
        Generate password reset token and send email
        """
        lawyer = db.query(Lawyer).filter(Lawyer.email == email).first()
        
        if not lawyer:
            # Don't reveal if email exists (security best practice)
            return {"message": "If email exists, password reset link has been sent"}

        # Generate reset token (valid for 30 minutes)
        reset_data = {
            "sub": lawyer.id,
            "type": "lawyer",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        reset_token = jwt.encode(reset_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Send email
        from utiles.email_service import EmailService
        email_sent = EmailService.send_password_reset_email(
            recipient_email=lawyer.email,
            recipient_name=lawyer.full_name,
            reset_token=reset_token,
            user_type="lawyer"
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
        Verify password reset token and extract lawyer info
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            if payload.get("type") != "lawyer":
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
        Reset lawyer password with valid token
        """
        # Verify token
        token_data = LawyerService.verify_reset_token(token)
        lawyer_id = token_data["id"]

        # Get lawyer
        lawyer = db.query(Lawyer).filter(Lawyer.id == lawyer_id).first()
        if not lawyer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lawyer not found"
            )

        # Update password
        lawyer.password = LawyerService.hash_password(new_password)
        db.commit()
        db.refresh(lawyer)

        return {"message": "Password reset successfully"}
