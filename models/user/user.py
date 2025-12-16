from sqlalchemy import Column, String, TIMESTAMP, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db.session import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )

    name = Column(String, nullable=False)

    email = Column(String, unique=True, index=True, nullable=False)

    phone_number = Column(String, unique=True, nullable=False)

    hashed_password = Column(String, nullable=False)

    role = Column(
        String,
        nullable=False,
        server_default="user"   # <-- DEFAULT ROLE
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    reviews = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    messages = relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan"
    )
