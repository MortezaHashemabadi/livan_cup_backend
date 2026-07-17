import random
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers

from .models import User, OTP, OTPPurpose, Address, BusinessProfile

PHONE_REGEX = r"^09\d{9}$"


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.RegexField(PHONE_REGEX, error_messages={"invalid": "شماره موبایل معتبر نیست"})
    purpose = serializers.ChoiceField(choices=OTPPurpose.choices, default=OTPPurpose.LOGIN)

    def create_otp(self):
        code = f"{random.randint(0, 999999):06d}"
        return OTP.objects.create(
            phone=self.validated_data["phone"],
            code=code,
            purpose=self.validated_data["purpose"],
            expires_at=timezone.now() + timedelta(minutes=2),
        )


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.RegexField(PHONE_REGEX)
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        otp = OTP.objects.filter(phone=data["phone"], code=data["code"]).order_by("-created_at").first()
        if not otp or not otp.is_valid():
            raise serializers.ValidationError("کد نامعتبر یا منقضی شده است")
        data["otp"] = otp
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "first_name", "last_name", "is_phone_verified", "date_joined"]
        read_only_fields = ["id", "phone", "is_phone_verified", "date_joined"]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "title", "province", "city", "full_address", "postal_code", "is_default"]

class BusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessProfile
        fields = ['business_name', 'business_type', 'economic_code', 'national_id','position']