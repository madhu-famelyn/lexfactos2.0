# config/db/session.py

import os
from datetime import timedelta, datetime, time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import pytz

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Only add sslmode=require if it's not localhost
if DATABASE_URL and "sslmode" not in DATABASE_URL:
    if not ("localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL):
        if "?" in DATABASE_URL:
            DATABASE_URL += "&sslmode=require"
        else:
            DATABASE_URL += "?sslmode=require"

# ------------------------------
# Create SQLAlchemy engine
# ------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,                # check connection before using
    pool_recycle=1800,                 # recycle connections every 30 mins
    pool_size=5,                       # keep 5 persistent connections
    max_overflow=10,                   # allow 10 extra connections if needed
    pool_timeout=30,                   # max wait time for a connection
    connect_args={"connect_timeout": 10}  # DB connection timeout
)

# ------------------------------
# Session factory
# ------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ------------------------------
# Base class for models
# ------------------------------
Base = declarative_base()

# ------------------------------
# Dependency for FastAPI routes
# ------------------------------
def get_db():
    """
    Provide a transactional scope around a series of operations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------
# Helper: IST timezone helper
# ------------------------------
IST = pytz.timezone("Asia/Kolkata")

def now_ist():
    """Return current datetime in IST."""
    return datetime.now(IST)

def midnight_ist():
    """Return next midnight datetime in IST."""
    today_ist = datetime.now(IST).date()
    midnight = datetime.combine(today_ist, time.min)
    return IST.localize(midnight) + timedelta(days=1)
