from sqlalchemy import Column, String, TIMESTAMP, text, JSON, Integer
from sqlalchemy.sql import func
from config.db.session import Base
from sqlalchemy.orm import relationship
import uuid


class Lawyer(Base):
    __tablename__ = "lawyers"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )

    lawyer_id = Column(
        String,
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    full_name = Column(String, nullable=False)

    address_line_1 = Column(String, nullable=False)

    status = Column(String, nullable=False, default="pending")
    rejected_reason = Column(String, nullable=True)
    position_status = Column(String, nullable=False, default="active")

    position_status = Column(
        String,
        nullable=False,
        default="non"
    )

    position_status_days = Column(
        Integer,
        nullable=True
    )

    position_status_expiry = Column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String, unique=True, nullable=False)

    # ✅ Store HASHED password only
    password = Column(String, nullable=False)

    website_link = Column(String, nullable=True)
    linkedin_link = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    bio = Column(String, nullable=True)
    practice_areas = Column(JSON, nullable=True)
    courts = Column(JSON, nullable=True)
    known_languages = Column(JSON, nullable=True)

    # ✅ NEW COLUMN — Years of Experience
    experience = Column(
        Integer,
        nullable=True
    )

    role = Column(String, nullable=False, default="lawyer")

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

    # -------------------------------
    # RELATIONSHIPS
    # -------------------------------

    reviews = relationship(
        "Review",
        back_populates="lawyer",
        cascade="all, delete-orphan"
    )

    messages = relationship(
        "Message",
        back_populates="lawyer",
        cascade="all, delete-orphan"
    )

