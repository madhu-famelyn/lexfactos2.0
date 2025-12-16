# models/models/review.py
from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.db.session import Base
import uuid

class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lawyer_id = Column(String, ForeignKey("lawyers.id", ondelete="CASCADE"), nullable=False, index=True)

    review = Column(String, nullable=True)
    rating = Column(Integer, nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 🔹 Use back_populates, NOT backref
    user = relationship("User", back_populates="reviews")
    lawyer = relationship("Lawyer", back_populates="reviews")
