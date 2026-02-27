"""
URL configuration for inventory_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from inventory.views import RegisterView,LoginView,LogoutView,PasswordResetRequestView,PasswordResetVerifyView,SetPasswordView,set_password,request_otp,login_view,admin_dashboard,signup_view,user_dashboard,reset_otp
from django.urls import path


urlpatterns = [
    path('admin/', admin.site.urls),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
     path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password-reset/verify/", PasswordResetVerifyView.as_view(), name="password_reset_verify"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path("user-dashboard/", user_dashboard, name="user_dashboard"),
    path("reset-otp/", reset_otp, name="reset-otp"),
    path("request-otp/", request_otp, name="request-otp"),
    path("setpassword/", set_password, name="setpassword"),
    path("set-password/", SetPasswordView.as_view(), name="set-password"),
    
]
