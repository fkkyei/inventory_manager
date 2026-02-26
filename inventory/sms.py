import requests
from django.conf import settings


def send_otp_sms(phone_number, otp_code):
    url = "https://api.ng.termii.com/api/sms/send"

    payload = {
        "to": phone_number,
        "from": settings.TERMII_SENDER_ID,
        "sms": f"Your inventory system verification code is: {otp_code}. It expires in 10 minutes.",
        "type": "plain",
        "channel": "dnd",
        "api_key": settings.TERMII_API_KEY,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"SMS sending failed: {e}")
        raise