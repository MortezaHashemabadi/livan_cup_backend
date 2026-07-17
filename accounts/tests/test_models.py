import pytest
from datetime import timedelta
from django.utils import timezone
from accounts.models import User, OTPPurpose
from accounts.tests.factories import UserFactory, OTPFactory

pytestmark = pytest.mark.django_db


class TestUserModel:
    def test_create_user_without_password_sets_unusable(self):
        user = User.objects.create_user(phone="09121112233")
        assert not user.has_usable_password()

    def test_create_user_requires_phone(self):
        with pytest.raises(ValueError):
            User.objects.create_user(phone="")

    def test_create_superuser_sets_flags(self):
        user = User.objects.create_superuser(phone="09121112233", password="strongpass")
        assert user.is_staff
        assert user.is_superuser
        assert user.has_usable_password()

    def test_create_superuser_requires_password(self):
        with pytest.raises(ValueError):
            User.objects.create_superuser(phone="09121112233", password=None)

    def test_str_returns_phone(self):
        user = UserFactory(phone="09121112233")
        assert str(user) == "09121112233"


class TestOTPModel:
    def test_otp_is_valid_when_fresh(self):
        otp = OTPFactory()
        assert otp.is_valid() is True

    def test_otp_invalid_when_expired(self):
        otp = OTPFactory(expires_at=timezone.now() - timedelta(seconds=1))
        assert otp.is_valid() is False

    def test_otp_invalid_when_used(self):
        otp = OTPFactory(is_used=True)
        assert otp.is_valid() is False