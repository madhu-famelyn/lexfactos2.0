from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


# ============================================================
# BASE FIELDS (USED BY: CREATE + EXCEL)
# ============================================================
class LawyerBase(BaseModel):
    full_name: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    country: str
    zip_code: str
    email: EmailStr
    phone_number: str

    website_link: Optional[str] = None
    linkedin_link: Optional[str] = None

    # ✅ NEW FIELD
    experience: Optional[int] = Field(
        None,
        ge=0,
        description="Total years of professional experience"
    )

    # This will store ONLY S3 URL after upload
    image_url: Optional[str] = None

    known_languages: Optional[List[str]] = None


# ============================================================
# CREATE → UI sends password + form fields
# ============================================================
class LawyerCreate(LawyerBase):
    password: str = Field(..., min_length=6)


# ============================================================
# UPDATE → For editing profile (NO password, NO role)
# ============================================================
class LawyerUpdate(BaseModel):
    full_name: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    website_link: Optional[str] = None
    linkedin_link: Optional[str] = None

    # ✅ NEW FIELD
    experience: Optional[int] = Field(
        None,
        ge=0
    )

    # ONLY S3 URL, image upload handled separately
    image_url: Optional[str] = None

    known_languages: Optional[List[str]] = None


# ============================================================
# STATUS UPDATE (Admin Only)
# ============================================================
class LawyerStatusUpdate(BaseModel):
    status: str
    rejected_reason: Optional[str] = None

    @validator("status")
    def validate_status(cls, value):
        allowed = ["pending", "approved", "rejected"]
        if value not in allowed:
            raise ValueError("Status must be pending, approved, or rejected")
        return value


# ============================================================
# RESPONSE SCHEMA (Password never returned)
# ============================================================
class LawyerResponse(BaseModel):
    id: str
    lawyer_id: str
    full_name: str
    address_line_1: str
    address_line_2: Optional[str]
    city: str
    state: str
    country: str
    zip_code: str
    email: EmailStr
    phone_number: str
    position_status: str

    # ✅ NEW FIELD
    experience: Optional[int]

    website_link: Optional[str]
    linkedin_link: Optional[str]
    image_url: Optional[str]
    known_languages: Optional[List[str]]

    role: str
    status: str
    rejected_reason: Optional[str]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# EXCEL UPLOAD → Excel SHOULD NOT send password
# ============================================================
class LawyerExcelUpload(BaseModel):
    full_name: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    country: str
    zip_code: str
    email: EmailStr
    phone_number: str
    website_link: Optional[str] = None
    linkedin_link: Optional[str] = None

    # ✅ NEW FIELD
    experience: Optional[int] = Field(
        None,
        ge=0
    )

    known_languages: Optional[List[str]] = None


class UpdateLawyerPositionRequest(BaseModel):
    position_status: str
    position_status_days: Optional[int] = Field(
        None,
        gt=0,
        description="Number of days the position should be active"
    )
