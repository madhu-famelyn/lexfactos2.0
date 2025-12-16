from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from models.user.user import User
from schemas.user.user import UserCreate, UserUpdate

# -------------------------------------------------
# Password hashing (kept here intentionally)
# -------------------------------------------------

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


# -------------------------------------------------
# User Service
# -------------------------------------------------

class UserService:
    """
    All user-related business logic lives here.
    Routers should NOT contain DB logic.
    """

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        # ---- check email uniqueness ----
        if db.query(User).filter(User.email == user_in.email).first():
            raise ValueError("Email already registered")

        # ---- check phone uniqueness ----
        if (
            db.query(User)
            .filter(User.phone_number == user_in.phone_number)
            .first()
        ):
            raise ValueError("Phone number already registered")

        # ---- create user ----
        user = User(
            name=user_in.name,
            email=user_in.email,
            phone_number=user_in.phone_number,
            hashed_password=hash_password(user_in.password),
        )

        db.add(user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Failed to create user")

        db.refresh(user)
        return user

    @staticmethod
    def update_user(
        db: Session,
        user: User,
        user_in: UserUpdate
    ) -> User:
        if user_in.name is not None:
            user.name = user_in.name

        if user_in.phone_number is not None:
            user.phone_number = user_in.phone_number

        if user_in.password is not None:
            user.hashed_password = hash_password(user_in.password)

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()
