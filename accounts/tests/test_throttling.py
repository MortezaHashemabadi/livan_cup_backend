import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


class TestOTPThrottle:
    def setup_method(self):
        cache.clear()

    def test_otp_rate_limit_blocks_after_threshold(self):
        client = APIClient()
        phone = "09123456789"
        # طبق settings: 'otp': '3/min'
        for _ in range(3):
            response = client.post("/api/accounts/otp/send/", {"phone": phone})
            assert response.status_code == 200

        response = client.post("/api/accounts/otp/send/", {"phone": phone})
        assert response.status_code == 429

    def test_different_phones_not_throttled_together(self):
        client = APIClient()
        for i in range(3):
            client.post("/api/accounts/otp/send/", {"phone": f"0912345678{i}"})
        # شماره چهارم، جدا از throttle قبلیاست
        response = client.post("/api/accounts/otp/send/", {"phone": "09123456799"})
        assert response.status_code == 200