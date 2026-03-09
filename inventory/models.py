from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import secrets
import random


class User(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("user", "User"),
    ]

    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    # 2FA fields
    phone_number = models.CharField(max_length=15)
    two_factor_enabled = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.email

    class Meta:
        app_label = "inventory"


class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes")
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    def __str__(self):
        return f"OTP({self.user.email})"

    class Meta:
        app_label = "inventory"


class SessionToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    @staticmethod
    def generate_token():
        return secrets.token_hex(32)

    def __str__(self):
        return f"Session({self.user.email})"

    class Meta:
        app_label = "inventory"

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_otps")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    def __str__(self):
        return f"PasswordResetOTP({self.user.email})"

    class Meta:
        app_label = "inventory"

        

class inventory(models.Model):
    
    status_choices =[
        ("In Stock","in stock"),
        ("Out Of Stock","out of stock")
         
    ]
    
    code= models.CharField(max_length=12, unique=True,null=False)
    item = models.CharField(max_length=250,null=False)
    total= models.IntegerField(null=False,default=0)
    allocated = models.IntegerField(null=False, default=0)
    available= models.IntegerField(null=False,default=0)
    utilization= models.IntegerField(null=False,default=0)
    status= models.CharField(max_length=250,choices=status_choices,default="In Stock")
    created_at  = models.DateTimeField(auto_now_add=True, null=True)

    def save(self,*args,**kwargs):
        
        if self.pk:
            old=inventory.objects.get(pk=self.pk)
            self.total=old.total+self.total
            self.allocated = old.allocated + self.allocated
        else:
            self.allocated = 0
        self.cascade_update()
        super().save(*args,**kwargs)
    
    def cascade_update(self):
        if self.total is not None and self.allocated is not None:
            self.available = self.total - self.allocated
            self.utilization = int((self.allocated / self.total) * 100) if self.total > 0 else 0
        

        
        self.status = "In Stock" if self.available > 0 else "Out Of Stock"

    

class report_request(models.Model):

    request_choices = [
        ('Full Allocation Report', 'Full Allocation Report'),
        ('Available Stock Summary', 'Available Stock Summary'),
        ('User Specific Report', 'User Specific Report'),
    ]

    date_range_choices = [
        ('All Time', 'All Time'),
        ('Last 7 Days', 'Last 7 Days'),
        ('Last 30 Days', 'Last 30 Days'),
        ('This Month', 'This Month'),
    ]

    export_format_choices = [
        ('csv', '.csv — Comma Separated'),
        ('xlsx', '.xlsx — Excel'),
        ('pdf', '.pdf — PDF'),
    ]

    report_configuration = models.CharField(max_length=256, choices=request_choices, default='Full Allocation Report')
    date_range           = models.CharField(max_length=256, choices=date_range_choices, default='All Time')
    export_format        = models.CharField(max_length=50,  choices=export_format_choices, default='csv')

class reservation(models.Model):
    status_choices = [
        ('Pending', 'Pending'),
        ('Checked Out', 'Checked Out'),
    ]
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_reservations'
    )
    inventory = models.ForeignKey(
        inventory,
        on_delete=models.CASCADE,
        related_name='item_reservations'
    )
    quantity = models.IntegerField(null=False)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=256, choices=status_choices, default='Pending')

    def save(self, *args, **kwargs):
        if self.pk:
            old = reservation.objects.get(pk=self.pk)

            # Pending → Checked Out: allocate stock
            if old.status == 'Pending' and self.status == 'Checked Out':
                if self.quantity > self.inventory.available:
                    raise ValueError("Quantity exceeds available stock")
                self.inventory.allocated += self.quantity
                self.inventory.save()

            # Checked Out → Pending: reverse allocation
            elif old.status == 'Checked Out' and self.status == 'Pending':
                self.inventory.allocated -= self.quantity
                self.inventory.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} — {self.inventory.item} x{self.quantity}"

    class Meta:
        app_label = "inventory"

        # always runs — saves the reservation

    

            
    



    
    

    


                             



