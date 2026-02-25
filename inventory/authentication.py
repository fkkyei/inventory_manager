from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from .models import SessionToken


class SessionTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get("Authorization")

        if not token or not token.startswith("Bearer "):
            return None

        raw_token = token.split(" ")[1]

        try:
            session = SessionToken.objects.select_related("user").get(
                token=raw_token,
                is_active=True,
            )
        except SessionToken.DoesNotExist:
            raise AuthenticationFailed("Invalid or expired session token")

        if session.expires_at < timezone.now():
            session.is_active = False
            session.save()
            raise AuthenticationFailed("Session has expired, please log in again")

        return (session.user, session)