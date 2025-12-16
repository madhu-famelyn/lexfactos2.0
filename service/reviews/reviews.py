from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.reviews.reviews import Review
from models.user.user import User
from models.lawyer.lawyer import Lawyer
from schemas.reviews.reviews import ReviewCreate, ReviewUpdate

class ReviewService:
    """
    Business logic for Reviews
    """

    @staticmethod
    def create_review(db: Session, review_in: ReviewCreate) -> Review:
        # Check if user exists
        user = db.query(User).filter(User.id == review_in.user_id).first()
        if not user:
            raise ValueError("User does not exist")

        # Check if lawyer exists
        lawyer = db.query(Lawyer).filter(Lawyer.id == review_in.lawyer_id).first()
        if not lawyer:
            raise ValueError("Lawyer does not exist")

        # Check if user already reviewed this lawyer
        existing = (
            db.query(Review)
            .filter(
                Review.user_id == review_in.user_id,
                Review.lawyer_id == review_in.lawyer_id
            )
            .first()
        )
        if existing:
            raise ValueError("User has already reviewed this lawyer")

        # Create review
        review = Review(
            user_id=review_in.user_id,
            lawyer_id=review_in.lawyer_id,
            review=review_in.review,
            rating=review_in.rating
        )

        db.add(review)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError("Failed to create review")
        db.refresh(review)

        return review

    @staticmethod
    def update_review(db: Session, review: Review, review_in: ReviewUpdate) -> Review:
        if review_in.review is not None:
            review.review = review_in.review

        if review_in.rating is not None:
            review.rating = review_in.rating

        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def get_review_by_id(db: Session, review_id: str) -> Review | None:
        return db.query(Review).filter(Review.id == review_id).first()

    @staticmethod
    def get_reviews_by_lawyer(db: Session, lawyer_id: str) -> list[Review]:
        return db.query(Review).filter(Review.lawyer_id == lawyer_id).all()

    @staticmethod
    def get_reviews_by_user(db: Session, user_id: str) -> list[Review]:
        return db.query(Review).filter(Review.user_id == user_id).all()
