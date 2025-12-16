from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from config.db.session import get_db

# DB

# Service
from service.user.user import UserService

# Schemas
from schemas.user.user import UserCreate, UserUpdate, UserRead

user_router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# -------------------------------------------------
# CREATE USER
# -------------------------------------------------
@user_router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    try:
        return UserService.create_user(db, user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# -------------------------------------------------
# GET USER BY ID
# -------------------------------------------------
@user_router.get(
    "/{user_id}",
    response_model=UserRead
)
def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db)
):
    user = UserService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


# -------------------------------------------------
# UPDATE USER
# -------------------------------------------------
@user_router.put(
    "/{user_id}",
    response_model=UserRead
)
def update_user(
    user_id: str,
    user_in: UserUpdate,
    db: Session = Depends(get_db)
):
    user = UserService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    try:
        return UserService.update_user(db, user, user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
