from sqlalchemy.orm import Session
from models.admin.admin import Admin
from schemas.admin.admin import AdminCreate, AdminUpdate
from passlib.context import CryptContext
import uuid
import re

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
