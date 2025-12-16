from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db.session import Base
import uuid

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    # -------------------------------------------------
    # Relations
    # -------------------------------------------------
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lawyer_id = Column(String, ForeignKey("lawyers.id", ondelete="CASCADE"), nullable=False, index=True)

    # -------------------------------------------------
    # User info (store snapshot of info at send time)
    # -------------------------------------------------
    email = Column(String, nullable=False)
    user_full_name = Column(String, nullable=False)
    user_phone_number = Column(String, nullable=False)

    # -------------------------------------------------
    # Message
    # -------------------------------------------------
    message = Column(String, nullable=False)

    # -------------------------------------------------
    # Timestamps
    # -------------------------------------------------
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # -------------------------------------------------
    # Relationships
    # -------------------------------------------------
    user = relationship("User", back_populates="messages")
    lawyer = relationship("Lawyer", back_populates="messages")
