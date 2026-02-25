from twilio.rest import Client
from django.conf import settings


def send_otp_sms(phone_number, otp_code):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f"Your inventory system verification code is: {otp_code}. It expires in 10 minutes.",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone_number,
    )
    return message.sid