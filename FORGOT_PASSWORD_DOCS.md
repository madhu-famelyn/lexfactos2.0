# Forgot Password Feature - Documentation

## Overview

Forgot password functionality has been integrated for **Lawyers**, **Users**, and **Admins**. The system uses JWT tokens with 30-minute expiry and email notifications via Brevo (SendinBlue).

## Required Environment Variables

Add these to your `.env` file:

```env
# Email Configuration (Brevo/SendinBlue)
BREVO_API_KEY=your_brevo_api_key_here
SENDER_EMAIL=noreply@lexfactos.com
SENDER_NAME=Lexfactos
FRONTEND_URL=http://localhost:3000

# JWT Configuration (already required)
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
```

## API Endpoints

### 1. Request Password Reset

**POST** `/auth/forgot-password`

Request a password reset link. An email with reset token will be sent to the user.

**Request Body (Form):**

```json
{
  "email": "lawyer@example.com",
  "role": "lawyer"
}
```

**Role options:**

- `lawyer` - Reset password for lawyer
- `user` - Reset password for regular user
- `admin` - Reset password for admin

**Response:**

```json
{
  "success": true,
  "message": "If email exists, password reset link has been sent"
}
```

### 2. Reset Password with Token

**POST** `/auth/reset-password`

Reset the password using the token received in the email.

**Request Body (JSON):**

```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "new_password": "NewSecurePassword123"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

## Email Template

Users receive an HTML email with:

- Reset link button
- Plain text backup link
- 30-minute expiry warning
- Security message

## Frontend Integration

### Step 1: Create Forgot Password Form

```html
<form action="/auth/forgot-password" method="post">
  <input type="email" name="email" placeholder="Enter email" required />
  <input type="hidden" name="role" value="lawyer" />
  <button type="submit">Send Reset Link</button>
</form>
```

### Step 2: Reset Password Page

When user clicks link from email, extract the token from URL:

```
http://your-frontend.com/reset-password?token=<JWT_TOKEN>&type=lawyer
```

Then send reset request:

```javascript
const response = await fetch("/auth/reset-password", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    token: urlParams.get("token"),
    new_password: newPasswordInput.value,
  }),
});
```

## Security Features

✅ **JWT Tokens** - 30-minute expiry  
✅ **Password Hashing** - Bcrypt hashed passwords  
✅ **Email Verification** - Brevo API integration  
✅ **Rate Limiting Ready** - Can be added with middleware  
✅ **Safe Responses** - Doesn't reveal if email exists

## Testing

### Test with cURL

**1. Request Reset:**

```bash
curl -X POST "http://127.0.0.1:8000/auth/forgot-password" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=lawyer@example.com&role=lawyer"
```

**2. Reset Password:**

```bash
curl -X POST "http://127.0.0.1:8000/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_TOKEN_HERE",
    "new_password": "NewPassword123"
  }'
```

## Files Modified/Created

### New Files:

- `utiles/email_service.py` - Email sending service
- `schemas/password_reset.py` - Password reset schemas

### Modified Files:

- `apis/admin/auth.py` - Added 2 new endpoints
- `service/lawyer/lawyer.py` - Added password reset methods
- `service/user/user.py` - Added password reset methods
- `service/admin/admin.py` - Added password reset methods

## Troubleshooting

**Issue: "BREVO_API_KEY is not set"**

- Add `BREVO_API_KEY` to your `.env` file

**Issue: "Failed to send reset email"**

- Check Brevo API key is valid
- Check email configuration
- Check SENDER_EMAIL is correct format

**Issue: "Reset token has expired"**

- Tokens expire after 30 minutes
- User must request new reset link

## Future Enhancements

Consider adding:

- Rate limiting on forgot password endpoint
- Admin dashboard to manage password resets
- SMS-based password resets (Twilio integration ready)
- Custom email templates
