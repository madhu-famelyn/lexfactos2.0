from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class AdminBase(BaseModel):
    full_name: str = Field(..., description="Full name of the admin")
    email: str = Field(..., description="Email address of the admin")
    mobile_number: str = Field(..., description="Mobile number of the admin")

class AdminCreate(AdminBase):
    password: str = Field(..., min_length=6, max_length=128, description="Password for the admin")

class AdminUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    password: Optional[str] = None

class AdminResponse(AdminBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
