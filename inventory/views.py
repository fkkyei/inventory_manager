from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import User, SessionToken, OTPCode, PasswordResetOTP
from .serializer import RegisterSerializer, UserSerializer,PasswordResetRequestSerializer,PasswordResetVerifySerializer,SetPasswordSerializer
from .authentication import SessionTokenAuthentication
from .permissions import IsAdmin, IsRegularUser
from .sms import send_otp_sms
from django.shortcuts import render
import random

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return render(request, 'signup.html')
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            send_mail(
                subject="Account Created Successfully",
                message=f"Hi {user.email},\n\nYour account has been created successfully.\n\nWelcome aboard!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

            return Response({
                "message": "User Registered Successfully",
                "user": UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return render(request, 'login.html')
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
        return render(request,'dashboard.html',{{"message":request.user.email,"role":request.user.role,"name":request.user}})



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
        "message":"Login Successful",
        "session_token": session.token,
        "role": user.role,
        "redirect": "/admin/dashboard" if user.role == "admin" else "/user-dashboard",
    })


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=serializer.validated_data["email"])

        # Invalidate any previous unused reset OTPs
        user.password_reset_otps.filter(is_used=False).update(is_used=True)

        otp = str(random.randint(100000, 999999))
        OTPCode.objects.create(
            user=user,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
            
        
        send_mail(
            subject="Password Reset OTP",
            message=f"Hi {user.email},\n\nYour password reset OTP is: {otp}\n\nThis OTP expires in 5 minutes.\n\nIf you did not request this, please ignore this email.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )


        

        return Response({
            "message": "Password reset OTP sent to your registered email.",
            "email": user.email,

        }, status=status.HTTP_200_OK)


from django.utils import timezone

class PasswordResetVerifyView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        otp_obj = user.otp_codes.filter(
            otp=code,
            is_used=False,
            expires_at__gt=timezone.now()
        ).last()

        if not otp_obj:
            return Response(
                {"error": "Invalid or expired OTP code"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        otp_obj.is_used = True
        otp_obj.save()

        return Response({"message": "OTP verified successfully"})
        
class SetPasswordView(APIView):
    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            
            return Response(
                {"message": "Password set successfully. Please login."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    

def admin_dashboard(request):
    return render(request, "admin_dashboard.html")
    
def login_view(request):
    return render(request, "login.html")
    
def signup_view(request):
    return render(request, "signup.html")


def user_dashboard(request):
    return render(request, "user_dashboard.html")

def reset_otp(request):
    return render(request, "enterresetotp.html")

def request_otp(request):
    return render(request, "requestotp.html")

def set_password(request):
    return render(request, "setpassword.html")
    

