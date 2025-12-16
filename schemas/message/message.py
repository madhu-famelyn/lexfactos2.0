from pydantic import BaseModel, EmailStr, Field

class MessageCreate(BaseModel):
    user_id: str = Field(..., description="ID of the user sending the message")
    lawyer_id: str = Field(..., description="ID of the lawyer receiving the message")
    email: EmailStr = Field(..., description="Email of the user")
    user_full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    user_phone_number: str = Field(..., min_length=10, max_length=15, description="Phone number of the user")
    message: str = Field(..., min_length=1, max_length=2000, description="The message content")
