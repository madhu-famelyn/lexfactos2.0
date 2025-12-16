from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.message.message import MessageCreate
from service.message.message import MessageService
from config.db.session import get_db

message_router = APIRouter(
    prefix="/messages",
    tags=["Messages"]
)

@message_router.post("/", response_model=dict)
def send_message(message_in: MessageCreate, db: Session = Depends(get_db)):
    """
    Send a message from a user to a lawyer.
    Saves message to DB and sends email to lawyer via Brevo.
    """
    try:
        message = MessageService.send_message(db, message_in)
        return {
            "status": "success",
            "message_id": message.id,
            "detail": f"Message sent to lawyer {message.lawyer_id}"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )
