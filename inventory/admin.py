from django.contrib import admin
from .models import User,OTPCode,SessionToken
from django.contrib.auth.hashers import make_password, check_password

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    # What you see in the main list
    list_display = ('email', 'role', 'is_active', 'two_factor_enabled', 'date_joined')
    fields = ('email', 'password', 'role', 'phone_number', 'two_factor_enabled', 'is_active')

    def save_model(self, request, obj, form, change):
        # Check if the password is already hashed (hashes usually start with 'pbkdf2_sha256$')
        if not obj.password.startswith('pbkdf2_sha256$'):
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

admin.site.register(User, UserAdmin)
