from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=15)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)



class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    password: Optional[str] = Field(None, min_length=8)

class UserRead(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Required for SQLAlchemy ORM objects
