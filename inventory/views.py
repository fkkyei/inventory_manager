from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from django.utils import timezone
from datetime import timedelta

from .models import User, SessionToken, OTPCode
from .serializer import RegisterSerializer, UserSerializer
from .authentication import SessionTokenAuthentication
from .permissions import IsAdmin, IsRegularUser
from .sms import send_otp_sms


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user": UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "Account is disabled"},
                status=status.HTTP_403_FORBIDDEN
            )

        # If 2FA is enabled send OTP and pause login
        if user.two_factor_enabled:
            # Invalidate any previous unused OTPs
            user.otp_codes.filter(is_used=False).update(is_used=True)

            otp = OTPCode.objects.create(
                user=user,
                code=OTPCode.generate_code(),
                expires_at=timezone.now() + timedelta(minutes=10),
            )
            send_otp_sms(user.phone_number, otp.code)
            return Response({
                "message": "OTP sent to your registered phone number.",
                "requires_otp": True,
                "email": user.email,
            }, status=status.HTTP_200_OK)

        # No 2FA — complete login normally
        return complete_login(user)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response(
                {"error": "Email and OTP code are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = user.otp_codes.filter(code=code, is_used=False).last()

        if not otp or not otp.is_valid():
            return Response(
                {"error": "Invalid or expired OTP code"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        otp.is_used = True
        otp.save()

        return complete_login(user)


class Enable2FAView(APIView):
    authentication_classes = [SessionTokenAuthentication]

    def post(self, request):
        user = request.user
        if user.two_factor_enabled:
            return Response(
                {"message": "2FA is already enabled"},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.two_factor_enabled = True
        user.save()
        return Response({
            "message": f"2FA enabled successfully. OTPs will be sent to {user.phone_number}"
        })


class Disable2FAView(APIView):
    authentication_classes = [SessionTokenAuthentication]

    def post(self, request):
        user = request.user
        if not user.two_factor_enabled:
            return Response(
                {"message": "2FA is already disabled"},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.two_factor_enabled = False
        user.save()
        return Response({"message": "2FA disabled successfully"})


class LogoutView(APIView):
    authentication_classes = [SessionTokenAuthentication]

    def post(self, request):
        token = request.auth
        if token:
            token.is_active = False
            token.save()
        return Response({"message": "Logged out successfully"})


class AdminDashboardView(APIView):
    authentication_classes = [SessionTokenAuthentication]
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({
            "message": f"Welcome to the admin dashboard, {request.user.email}",
            "role": request.user.role,
        })


class UserDashboardView(APIView):
    authentication_classes = [SessionTokenAuthentication]
    permission_classes = [IsRegularUser]

    def get(self, request):
        return Response({
            "message": f"Welcome to your dashboard, {request.user.email}",
            "role": request.user.role,
        })


def complete_login(user):
    user.sessions.filter(is_active=True).update(is_active=False)
    session = SessionToken.objects.create(
        user=user,
        token=SessionToken.generate_token(),
        expires_at=timezone.now() + timedelta(days=7),
    )
    return Response({
        "user": UserSerializer(user).data,
        "session_token": session.token,
        "role": user.role,
        "redirect": "/admin/dashboard" if user.role == "admin" else "/dashboard",
    })