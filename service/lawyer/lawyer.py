from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException, status
from passlib.context import CryptContext
from models.lawyer.lawyer import Lawyer
from sqlalchemy import func, or_, cast, String
from sqlalchemy import func
from sqlalchemy import func, or_
from schemas.lawyer.lawyer import (
    LawyerCreate,
    LawyerUpdate,
    LawyerStatusUpdate,
    LawyerExcelUpload
)
import uuid
import json
import math


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

        # 1️⃣ Upload image if present
        if file:
            from utiles.s3_service import upload_to_s3
            image_url = upload_to_s3(file)
            data["image_url"] = image_url

        # 2️⃣ VALIDATIONS
        LawyerService._validate_full_name(data["full_name"])
        LawyerService._validate_email(data["email"])
        # Phone validation removed as you requested

        # 3️⃣ Duplicate checks
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

        # 4️⃣ Hash password
        data["password"] = LawyerService.hash_password(data["password"])

        data.update({
            "lawyer_id": str(uuid.uuid4()),
            "role": "lawyer",
            "status": "pending",
            "rejected_reason": None
        })

        # 5️⃣ Save in DB
        obj = Lawyer(**data)
        db.add(obj)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate entry found (email or phone)."
            )

        db.refresh(obj)
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
        LawyerService._validate_rejected_reason(status_data.status, status_data.rejected_reason)

        lawyer.status = status_data.status
        lawyer.rejected_reason = status_data.rejected_reason

        db.commit()
        db.refresh(lawyer)
        return lawyer

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
    # BULK CREATE FROM EXCEL WITH FULL VALIDATION
    # ============================================================


    FIXED_IMAGE_URL = "https://fliplyn-assets.s3.ap-south-1.amazonaws.com/lawyers/f377e72b-1414-49d2-be61-7f7d78376497.png"

    @staticmethod
    def bulk_create_lawyers(db: Session, lawyers: List[LawyerExcelUpload]):
        created_lawyers = []

        for data in lawyers:

            # Clean null / nan from Excel
            clean = {k: LawyerService._safe(v) for k, v in data.dict().items()}

            # Mandatory validations
            LawyerService._validate_full_name(clean["full_name"])
            LawyerService._validate_email(clean["email"])

            # Generate random password
            random_password = uuid.uuid4().hex[:10]
            hashed_password = LawyerService.hash_password(random_password)

            lawyer = Lawyer(
                full_name=clean["full_name"],
                address_line_1=clean["address_line_1"],
                address_line_2=clean["address_line_2"],
                city=clean["city"],
                state=clean["state"],
                country=clean["country"],
                zip_code=clean["zip_code"],
                email=clean["email"],
                phone_number=clean["phone_number"],
                website_link=clean["website_link"],
                linkedin_link=clean["linkedin_link"],
                image_url=LawyerService.FIXED_IMAGE_URL,   # <-- always set
                known_languages=clean.get("known_languages"),
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

        # Normalize
        country = country.strip().lower()

        # Always filter by country first
        query = db.query(Lawyer).filter(
            func.lower(Lawyer.country) == country
        )

        # If keyword exists, apply extra filters
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

        # Pagination
        if start < 1:
            start = 1
        if end < start:
            end = start + 9

        limit = end - start + 1
        offset = start - 1

        results = query.offset(offset).limit(limit).all()

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No lawyers found matching the criteria."
            )

        return results