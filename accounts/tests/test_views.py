import pytest
from rest_framework.test import APIClient
from accounts.tests.factories import UserFactory, OTPFactory, AddressFactory

pytestmark = pytest.mark.django_db


class TestSendOTP:
    def test_send_otp_success(self):
        client = APIClient()
        response = client.post("/api/accounts/otp/send/", {"phone": "09123456789"})
        assert response.status_code == 200

    def test_send_otp_invalid_phone(self):
        client = APIClient()
        response = client.post("/api/accounts/otp/send/", {"phone": "123"})
        assert response.status_code == 400


class TestVerifyOTP:
    def test_verify_creates_new_user_and_returns_jwt(self):
        OTPFactory(phone="09123456789", code="111111")
        client = APIClient()
        response = client.post("/api/accounts/otp/verify/", {"phone": "09123456789", "code": "111111"})
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["created"] is True

    def test_verify_existing_user_created_false(self):
        UserFactory(phone="09123456789")
        OTPFactory(phone="09123456789", code="111111")
        client = APIClient()
        response = client.post("/api/accounts/otp/verify/", {"phone": "09123456789", "code": "111111"})
        assert response.data["created"] is False

    def test_verify_wrong_code_fails(self):
        OTPFactory(phone="09123456789", code="111111")
        client = APIClient()
        response = client.post("/api/accounts/otp/verify/", {"phone": "09123456789", "code": "000000"})
        assert response.status_code == 400

    def test_verify_marks_otp_as_used(self):
        otp = OTPFactory(phone="09123456789", code="111111")
        client = APIClient()
        client.post("/api/accounts/otp/verify/", {"phone": "09123456789", "code": "111111"})
        otp.refresh_from_db()
        assert otp.is_used is True


class TestMeView:
    def test_requires_authentication(self):
        client = APIClient()
        response = client.get("/api/accounts/me/")
        assert response.status_code == 401

    def test_authenticated_user_can_view_profile(self):
        user = UserFactory(phone="09123456789")
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/accounts/me/")
        assert response.status_code == 200
        assert response.data["phone"] == "09123456789"


class TestAddressViews:
    def test_list_requires_auth(self):
        client = APIClient()
        response = client.get("/api/accounts/addresses/")
        assert response.status_code == 401

    def test_user_only_sees_own_addresses(self):
        user1 = UserFactory()
        user2 = UserFactory()
        AddressFactory(user=user1)
        AddressFactory(user=user2)

        client = APIClient()
        client.force_authenticate(user=user1)
        response = client.get("/api/accounts/addresses/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_create_address_assigns_current_user(self):
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post("/api/accounts/addresses/", {
            "title": "خانه",
            "province": "تهران",
            "city": "تهران",
            "full_address": "خیابان ولیعصر",
            "postal_code": "1111111111",
        })
        assert response.status_code == 201
        assert response.data["title"] == "خانه"