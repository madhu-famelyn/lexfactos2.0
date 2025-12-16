import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models.message.message import Message
from models.user.user import User
from models.lawyer.lawyer import Lawyer
from schemas.message.message import MessageCreate
from sib_api_v3_sdk import ApiClient, Configuration, TransactionalEmailsApi
from sib_api_v3_sdk.models.send_smtp_email import SendSmtpEmail 


load_dotenv()
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@fliplyn.com")
FROM_NAME = os.getenv("FROM_NAME", "Neos OTP System")


def send_email_to_lawyer(to_email: str, subject: str, html_content: str):
    """
    Sends an email to the lawyer using Brevo API.
    """
    configuration = Configuration()
    configuration.api_key["api-key"] = BREVO_API_KEY

    api_client = ApiClient(configuration)
    api_instance = TransactionalEmailsApi(api_client)

    email = SendSmtpEmail(
        to=[{"email": to_email}],
        sender={"email": FROM_EMAIL, "name": FROM_NAME},
        subject=subject,
        html_content=html_content
    )

    try:
        api_instance.send_transac_email(email)
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise ValueError(f"Failed to send message: {e}")


class MessageService:

    @staticmethod
    def send_message(db: Session, message_in: MessageCreate) -> Message:
        # Check user existence
        user = db.query(User).filter(User.id == message_in.user_id).first()
        if not user:
            raise ValueError("User does not exist")

        # Check lawyer existence
        lawyer = db.query(Lawyer).filter(Lawyer.id == message_in.lawyer_id).first()
        if not lawyer:
            raise ValueError("Lawyer does not exist")

        # Create message record
        message = Message(
            user_id=message_in.user_id,
            lawyer_id=message_in.lawyer_id,
            email=message_in.email,
            user_full_name=message_in.user_full_name,
            user_phone_number=message_in.user_phone_number,
            message=message_in.message
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        # Send email to lawyer
        subject = f"New message from {message_in.user_full_name}"
        html_content = f"""
        <p>You have received a new message from a user:</p>
        <p><strong>Name:</strong> {message_in.user_full_name}</p>
        <p><strong>Email:</strong> {message_in.email}</p>
        <p><strong>Phone:</strong> {message_in.user_phone_number}</p>
        <p><strong>Message:</strong><br>{message_in.message}</p>
        """
        send_email_to_lawyer(lawyer.email, subject, html_content)

        return message
