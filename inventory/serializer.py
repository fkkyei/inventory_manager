from rest_framework import serializers
from .models import User, OTPCode, inventory,reservation


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    phone_number = serializers.CharField(max_length=15)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            phone_number=validated_data["phone_number"],
            role="user",
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, read_only=True)
    phone_number = serializers.CharField(read_only=True)
    two_factor_enabled = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email.")
        return value


class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class SetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def save(self):
        email = self.validated_data["email"]
        password = self.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        user.set_password(password)
        user.save()
        return user


class inventoryserializer(serializers.ModelSerializer):
    total = serializers.IntegerField(required=True)

    class Meta:
        model = inventory
        fields = ['code', 'item', 'total', 'allocated', 'available', 'utilization', 'status']
        read_only_fields = ['allocated', 'available', 'utilization', 'status']

    def create(self, validated_data):
        record = inventory.objects.create(**validated_data)
        return record


class ReportRequestSerializer(serializers.Serializer):
    report_type = serializers.CharField(max_length=50, required=False, default="full")
    email = serializers.EmailField(required=False)


class ReservationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    item_available = serializers.IntegerField(source='inventory.available', read_only=True)
    inventory = serializers.PrimaryKeyRelatedField(
        queryset=inventory.objects.filter(status='In Stock')
    )

    class Meta:
        model = reservation
        fields = [
            'id',
            'user_email',
            'inventory',
            'quantity',
            'date',
            'status',
        ]
        read_only_fields = ['id', 'user_email','date', 'status']

    def validate(self, data):
        inventory_item = data.get('inventory')
        quantity = data.get('quantity')

        if quantity <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")

        if quantity > inventory_item.available:
            raise serializers.ValidationError(
                f"Only {inventory_item.available} units available for {inventory_item.item}."
            )

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    