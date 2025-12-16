from pydantic import BaseModel, Field, conint
from typing import Optional
from datetime import datetime

# -------------------------------------------------
# Base schema (shared fields)
# -------------------------------------------------
class ReviewBase(BaseModel):
    review: Optional[str] = Field(None, max_length=1000)
    rating: conint(ge=1, le=5)  # Rating must be 1–5


# -------------------------------------------------
# Create schema
# -------------------------------------------------
class ReviewCreate(ReviewBase):
    user_id: str
    lawyer_id: str


# -------------------------------------------------
# Update schema (partial update)
# -------------------------------------------------
class ReviewUpdate(BaseModel):
    review: Optional[str] = Field(None, max_length=1000)
    rating: Optional[conint(ge=1, le=5)]


# -------------------------------------------------
# Read schema
# -------------------------------------------------
class ReviewRead(ReviewBase):
    id: str
    user_id: str
    lawyer_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Required for SQLAlchemy ORM objects
