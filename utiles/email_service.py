import os
from dotenv import load_dotenv
from sib_api_v3_sdk.rest import ApiException
import sib_api_v3_sdk
from sib_api_v3_sdk.models.send_smtp_email import SendSmtpEmail

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("FROM_EMAIL", os.getenv("SENDER_EMAIL", "noreply@lexfactos.com"))
SENDER_NAME = os.getenv("FROM_NAME", os.getenv("SENDER_NAME", "Lexfactos"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

if not BREVO_API_KEY:
    raise RuntimeError("BREVO_API_KEY is not set in environment variables")


class EmailService:
    """Service for sending emails via Brevo (SendinBlue)"""

    @staticmethod
    def _get_client():
        """Initialize Brevo API client"""
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        return api_instance

    @staticmethod
    def send_password_reset_email(recipient_email: str, recipient_name: str, reset_token: str, user_type: str) -> bool:
        """
        Send password reset email with token

        Args:
            recipient_email: Email to send to
            recipient_name: Full name of recipient
            reset_token: JWT reset token
            user_type: 'lawyer', 'user', or 'admin'

        Returns:
            bool: True if sent successfully
        """
        try:
            print(f"\n[Email] Attempting to send password reset email...")
            print(f"   To: {recipient_email} ({recipient_name})")
            print(f"   From: {SENDER_EMAIL}")
            print(f"   Type: {user_type}")
            
            api_instance = EmailService._get_client()

            # Build reset link
            reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}&type={user_type}"

            email = SendSmtpEmail(
                to=[{"email": recipient_email, "name": recipient_name}],
                sender={"name": SENDER_NAME, "email": SENDER_EMAIL},
                subject="Reset Your Lexfactos Password",
                html_content=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                            <h2 style="color: #2c3e50;">Password Reset Request</h2>
                            
                            <p>Hello {recipient_name},</p>
                            
                            <p>We received a request to reset your password for your Lexfactos account.</p>
                            
                            <p>Click the button below to reset your password:</p>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{reset_link}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                    Reset Password
                                </a>
                            </div>
                            
                            <p>Or copy this link in your browser:</p>
                            <p style="background-color: #f5f5f5; padding: 10px; border-radius: 3px; word-break: break-all;">
                                {reset_link}
                            </p>
                            
                            <p><strong>This link will expire in 30 minutes.</strong></p>
                            
                            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                            
                            <p style="color: #7f8c8d; font-size: 12px;">
                                If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
                            </p>
                            
                            <p style="color: #7f8c8d; font-size: 12px;">
                                Best regards,<br>
                                <strong>Lexfactos Team</strong>
                            </p>
                        </div>
                    </body>
                </html>
                """
            )

            api_instance.send_transac_email(email)
            print(f"[Success] Email sent successfully to {recipient_email}")
            return True

        except ApiException as e:
            print(f"[Error] Brevo API Exception: {e.status} - {e.reason}")
            print(f"   Details: {e.body}")
            return False
        except Exception as e:
            print(f"[Error] Error sending email: {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def send_profile_under_review_email(recipient_email: str, recipient_name: str) -> bool:
        """Send email to lawyer when their profile is submitted and is under admin review"""
        try:
            print(f"\n[Email] Sending 'Profile Under Review' email to {recipient_email}...")
            api_instance = EmailService._get_client()

            email = SendSmtpEmail(
                to=[{"email": recipient_email, "name": recipient_name}],
                sender={"name": SENDER_NAME, "email": SENDER_EMAIL},
                subject="Your Lexfactos Profile is Under Review",
                html_content=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4;">
                        <div style="max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <div style="background-color: #1a3c6e; padding: 30px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Lexfactos</h1>
                            </div>
                            <div style="padding: 35px 40px;">
                                <h2 style="color: #1a3c6e; margin-top: 0;">Profile Submitted Successfully!</h2>
                                <p>Hello <strong>{recipient_name}</strong>,</p>
                                <p>Thank you for registering on <strong>Lexfactos</strong>! Your lawyer profile has been submitted and is currently <strong>under review</strong> by our admin team.</p>

                                <div style="background-color: #fff8e1; border-left: 4px solid #f5a623; padding: 15px 20px; margin: 25px 0; border-radius: 4px;">
                                    <p style="margin: 0; color: #856404;"><strong>⏳ Status: Under Review</strong></p>
                                    <p style="margin: 8px 0 0 0; font-size: 14px; color: #856404;">Our team will verify your credentials and activate your profile shortly. This usually takes 1–2 business days.</p>
                                </div>

                                <p>We will send you another email once your profile has been reviewed. You do <strong>not</strong> need to do anything at this time.</p>

                                <p style="color: #7f8c8d; font-size: 13px; margin-top: 30px;">
                                    If you have any questions, feel free to reach out to our support team.<br><br>
                                    Best regards,<br>
                                    <strong>Lexfactos Team</strong>
                                </p>
                            </div>
                        </div>
                    </body>
                </html>
                """
            )

            api_instance.send_transac_email(email)
            print(f"[Success] 'Profile Under Review' email sent to {recipient_email}")
            return True

        except ApiException as e:
            print(f"[Error] Brevo API Exception (profile review): {e.status} - {e.reason}")
            print(f"   Details: {e.body}")
            return False
        except Exception as e:
            print(f"[Error] Error sending profile review email: {type(e).__name__} - {e}")
            return False

    @staticmethod
    def send_profile_status_update_email(recipient_email: str, recipient_name: str, status: str, rejected_reason: str = None) -> bool:
        """
        Send email to lawyer when admin approves or rejects their profile.
        status: 'approved' or 'rejected'
        """
        try:
            print(f"\n[Email] Sending 'Profile {status.capitalize()}' email to {recipient_email}...")
            api_instance = EmailService._get_client()

            if status == "approved":
                subject = "🎉 Your Lexfactos Profile is Approved!"
                status_block = f"""
                <div style="background-color: #e6f9f0; border-left: 4px solid #28a745; padding: 15px 20px; margin: 25px 0; border-radius: 4px;">
                    <p style="margin: 0; color: #155724;"><strong>✅ Status: Approved</strong></p>
                    <p style="margin: 8px 0 0 0; font-size: 14px; color: #155724;">Your profile is now live on Lexfactos and visible to clients. You can log in to your account to manage your profile.</p>
                </div>
                <p>Congratulations! You are now a verified lawyer on Lexfactos. Start receiving client inquiries by keeping your profile up to date.</p>
                """
            else:
                subject = "Update on Your Lexfactos Profile Application"
                reason_text = f"<p><strong>Reason:</strong> {rejected_reason}</p>" if rejected_reason else ""
                status_block = f"""
                <div style="background-color: #fdecea; border-left: 4px solid #dc3545; padding: 15px 20px; margin: 25px 0; border-radius: 4px;">
                    <p style="margin: 0; color: #721c24;"><strong>❌ Status: Not Approved</strong></p>
                    <p style="margin: 8px 0 0 0; font-size: 14px; color: #721c24;">Unfortunately, your profile could not be approved at this time.</p>
                    {reason_text}
                </div>
                <p>Please review the reason above and contact our support team if you believe this was a mistake or need guidance on resubmitting.</p>
                """

            email = SendSmtpEmail(
                to=[{"email": recipient_email, "name": recipient_name}],
                sender={"name": SENDER_NAME, "email": SENDER_EMAIL},
                subject=subject,
                html_content=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4;">
                        <div style="max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <div style="background-color: #1a3c6e; padding: 30px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Lexfactos</h1>
                            </div>
                            <div style="padding: 35px 40px;">
                                <h2 style="color: #1a3c6e; margin-top: 0;">Profile Review Update</h2>
                                <p>Hello <strong>{recipient_name}</strong>,</p>
                                <p>Our admin team has reviewed your Lexfactos lawyer profile. Here is the update:</p>
                                {status_block}
                                <p style="color: #7f8c8d; font-size: 13px; margin-top: 30px;">
                                    Best regards,<br>
                                    <strong>Lexfactos Team</strong>
                                </p>
                            </div>
                        </div>
                    </body>
                </html>
                """
            )

            api_instance.send_transac_email(email)
            print(f"[Success] 'Profile {status.capitalize()}' email sent to {recipient_email}")
            return True

        except ApiException as e:
            print(f"[Error] Brevo API Exception (profile status): {e.status} - {e.reason}")
            print(f"   Details: {e.body}")
            return False
        except Exception as e:
            print(f"[Error] Error sending profile status email: {type(e).__name__} - {e}")
            return False

    @staticmethod
    def send_welcome_email(recipient_email: str, recipient_name: str, user_type: str) -> bool:
        """Send welcome email to new user"""
        try:
            api_instance = EmailService._get_client()

            email = SendSmtpEmail(
                to=[{"email": recipient_email, "name": recipient_name}],
                sender={"name": SENDER_NAME, "email": SENDER_EMAIL},
                subject="Welcome to Lexfactos!",
                html_content=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #2c3e50;">Welcome to Lexfactos!</h2>
                            <p>Hello {recipient_name},</p>
                            <p>Your account has been successfully created.</p>
                            <p>You can now log in with your credentials.</p>
                        </div>
                    </body>
                </html>
                """
            )

            api_instance.send_transac_email(email)
            return True

        except Exception as e:
            print(f"Error sending welcome email: {e}")
            return False
