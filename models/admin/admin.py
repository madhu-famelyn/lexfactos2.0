from sqlalchemy import Column, String, TIMESTAMP, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db.session import Base
import uuid

class Admin(Base):
    __tablename__ = "admins"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mobile_number = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # <-- Added password field

    role = Column(String, nullable=False, default="admin")  # <-- New role field

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
