from django.urls import path
from .views import RegisterView, LoginView, LogoutView, AdminDashboardView, UserDashboardView,VerifyOTPView,Enable2FAView,Disable2FAView,PasswordResetRequestView,PasswordResetVerifyView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path("dashboard/", UserDashboardView.as_view(), name="user_dashboard"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("2fa/enable/", Enable2FAView.as_view(), name="enable_2fa"),
    path("2fa/disable/", Disable2FAView.as_view(), name="disable_2fa"),
     # Password Reset
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password-reset/verify/", PasswordResetVerifyView.as_view(), name="password_reset_verify"),
]