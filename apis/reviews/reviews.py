from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from config.db.session import get_db
from service.reviews.reviews import ReviewService
from schemas.reviews.reviews import ReviewCreate, ReviewUpdate, ReviewRead
from models.reviews.reviews import Review

review_router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)

# -------------------------------------------------
# CREATE REVIEW
# -------------------------------------------------
@review_router.post(
    "/",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED
)
def create_review(
    review_in: ReviewCreate,
    db: Session = Depends(get_db)
):
    try:
        review = ReviewService.create_review(db, review_in)
        return review
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# -------------------------------------------------
# GET REVIEW BY ID
# -------------------------------------------------
@review_router.get(
    "/{review_id}",
    response_model=ReviewRead
)
def get_review_by_id(
    review_id: str,
    db: Session = Depends(get_db)
):
    review = ReviewService.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    return review

# -------------------------------------------------
# UPDATE REVIEW
# -------------------------------------------------
@review_router.put(
    "/{review_id}",
    response_model=ReviewRead
)
def update_review(
    review_id: str,
    review_in: ReviewUpdate,
    db: Session = Depends(get_db)
):
    review = ReviewService.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    try:
        updated_review = ReviewService.update_review(db, review, review_in)
        return updated_review
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# -------------------------------------------------
# GET ALL REVIEWS FOR A LAWYER
# -------------------------------------------------
@review_router.get(
    "/lawyer/{lawyer_id}",
    response_model=List[ReviewRead]
)
def get_reviews_for_lawyer(
    lawyer_id: str,
    db: Session = Depends(get_db)
):
    return ReviewService.get_reviews_by_lawyer(db, lawyer_id)

# -------------------------------------------------
# GET ALL REVIEWS BY A USER
# -------------------------------------------------
@review_router.get(
    "/user/{user_id}",
    response_model=List[ReviewRead]
)
def get_reviews_by_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    return ReviewService.get_reviews_by_user(db, user_id)
