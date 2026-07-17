from django.test import TestCase

# Create your tests here.
import pytest
from datetime import timedelta
from django.utils import timezone

from accounts.models import OTP, OTPPurpose, User


@pytest.mark.django_db
def test_send_otp_creates_otp_record(api_client):
    phone = "09121111111"
    response = api_client.post("/api/accounts/otp/send/", {"phone": phone, "purpose": OTPPurpose.LOGIN})

    assert response.status_code == 200
    otp = OTP.objects.filter(phone=phone).latest("created_at")
    assert len(otp.code) == 6
    assert otp.is_used is False
    assert otp.expires_at > timezone.now()


@pytest.mark.django_db
def test_send_otp_invalid_phone_rejected(api_client):
    response = api_client.post("/api/accounts/otp/send/", {"phone": "12345"})
    assert response.status_code == 400


@pytest.mark.django_db
def test_verify_otp_creates_user_and_returns_jwt(api_client):
    phone = "09122222222"
    api_client.post("/api/accounts/otp/send/", {"phone": phone})
    otp = OTP.objects.filter(phone=phone).latest("created_at")

    response = api_client.post("/api/accounts/otp/verify/", {"phone": phone, "code": otp.code})

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["created"] is True

    user = User.objects.get(phone=phone)
    assert user.is_phone_verified is True


@pytest.mark.django_db
def test_verify_otp_wrong_code_rejected(api_client):
    phone = "09123333333"
    api_client.post("/api/accounts/otp/send/", {"phone": phone})

    response = api_client.post("/api/accounts/otp/verify/", {"phone": phone, "code": "000000"})
    assert response.status_code == 400


@pytest.mark.django_db
def test_verify_otp_cannot_be_reused(api_client):
    phone = "09124444444"
    api_client.post("/api/accounts/otp/send/", {"phone": phone})
    otp = OTP.objects.filter(phone=phone).latest("created_at")

    first = api_client.post("/api/accounts/otp/verify/", {"phone": phone, "code": otp.code})
    assert first.status_code == 200

    second = api_client.post("/api/accounts/otp/verify/", {"phone": phone, "code": otp.code})
    assert second.status_code == 400


@pytest.mark.django_db
def test_expired_otp_rejected(api_client):
    phone = "09125555555"
    otp = OTP.objects.create(
        phone=phone,
        code="123456",
        purpose=OTPPurpose.LOGIN,
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    response = api_client.post("/api/accounts/otp/verify/", {"phone": phone, "code": otp.code})
    assert response.status_code == 400


@pytest.mark.django_db
def test_me_endpoint_requires_authentication(api_client):
    response = api_client.get("/api/accounts/me/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_me_endpoint_returns_authenticated_user(api_client):
    phone = "09126666666"
    api_client.post("/api/accounts/otp/send/", {"phone": phone})
    otp = OTP.objects.filter(phone=phone).latest("created_at")
    verify_response = api_client.post("/api/accounts/otp/verify/", {"phone": phone, "code": otp.code})
    access_token = verify_response.data["access"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    response = api_client.get("/api/accounts/me/")

    assert response.status_code == 200
    assert response.data["phone"] == phone


@pytest.mark.django_db
def test_otp_send_throttle(api_client):
    phone = "09127777777"

    for _ in range(3):
        response = api_client.post("/api/accounts/otp/send/", {"phone": phone})
        assert response.status_code == 200

    response = api_client.post("/api/accounts/otp/send/", {"phone": phone})
    assert response.status_code == 429