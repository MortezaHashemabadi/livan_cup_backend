import pytest
from accounts.serializers import SendOTPSerializer, VerifyOTPSerializer
from accounts.tests.factories import OTPFactory
from accounts.models import OTPPurpose

pytestmark = pytest.mark.django_db


class TestSendOTPSerializer:
    def test_valid_phone_creates_otp(self):
        serializer = SendOTPSerializer(data={"phone": "09123456789"})
        assert serializer.is_valid()
        otp = serializer.create_otp()
        assert otp.phone == "09123456789"
        assert len(otp.code) == 6

    @pytest.mark.parametrize("bad_phone", ["123", "0912345678", "0812345678", "abcdefghij"])
    def test_invalid_phone_rejected(self, bad_phone):
        serializer = SendOTPSerializer(data={"phone": bad_phone})
        assert not serializer.is_valid()

    def test_default_purpose_is_login(self):
        serializer = SendOTPSerializer(data={"phone": "09123456789"})
        serializer.is_valid()
        assert serializer.validated_data["purpose"] == OTPPurpose.LOGIN


class TestVerifyOTPSerializer:
    def test_valid_otp_passes(self):
        otp = OTPFactory(phone="09123456789", code="111111")
        serializer = VerifyOTPSerializer(data={"phone": "09123456789", "code": "111111"})
        assert serializer.is_valid()
        assert serializer.validated_data["otp"] == otp

    def test_wrong_code_fails(self):
        OTPFactory(phone="09123456789", code="111111")
        serializer = VerifyOTPSerializer(data={"phone": "09123456789", "code": "999999"})
        assert not serializer.is_valid()

    def test_used_otp_fails(self):
        OTPFactory(phone="09123456789", code="111111", is_used=True)
        serializer = VerifyOTPSerializer(data={"phone": "09123456789", "code": "111111"})
        assert not serializer.is_valid()

    def test_expired_otp_fails(self):
        from django.utils import timezone
        from datetime import timedelta
        OTPFactory(phone="09123456789", code="111111", expires_at=timezone.now() - timedelta(seconds=1))
        serializer = VerifyOTPSerializer(data={"phone": "09123456789", "code": "111111"})
        assert not serializer.is_valid()