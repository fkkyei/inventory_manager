from django.core.mail import send_mail
from django.conf import settings


def send_password_reset_email(email, otp_code):
    try:
        send_mail(
            subject="Password Reset OTP",
            message=f"""
You requested a password reset for your Inventory System account.

Your OTP code is: {otp_code}

This code expires in 10 minutes.

If you did not request this, please ignore this email.
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email sending failed: {e}")
        raise