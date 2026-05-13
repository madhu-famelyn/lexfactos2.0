from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class ForgotPasswordRequest(BaseModel):
    """Request to initiate password reset"""
    email: EmailStr
    role: str = Field(default="user", description="Role: lawyer, user, or admin")


class ResetPasswordRequest(BaseModel):
    """Request to reset password with token"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=6, description="New password (min 6 chars)")


class PasswordResetResponse(BaseModel):
    """Response for password reset operations"""
    success: bool
    message: str
