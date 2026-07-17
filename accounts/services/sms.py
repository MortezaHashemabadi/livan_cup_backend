from pathlib import Path
import environ
from abc import ABC, abstractmethod
from django.conf import settings
import requests
import logging

BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / '.env')
env = environ.Env()
logger = logging.getLogger(__name__)


class SMSProvider(ABC):
    @abstractmethod
    def send_otp(self, phone: str, code: str) -> bool:
        ...


class ConsoleSMSProvider(SMSProvider):
    """برای dev: کد رو فقط توی ترمینال چاپ می‌کنه"""

    def send_otp(self, phone: str, code: str) -> bool:
        print(f"[OTP] به {phone} ارسال شد: {code}")
        return True


class KavenegarSMSProvider(SMSProvider):
    def send_otp(self, phone: str, code: str) -> bool:
        url = "https://api.sms.ir/v1/send/verify"
        api_key = env('SMS_API_KEY')
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        formatted_phone = phone.lstrip('0')
        payload = {
            "mobile": formatted_phone,
            "templateId": 570670,
            "parameters": [
                {
                    "name": code,
                    "value": "12345"
                }
            ]
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)

            response.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"خطا در ارسال پیامک به {phone}: {e}")
            return False


def get_sms_provider() -> SMSProvider:
    name = getattr(settings, "SMS_PROVIDER", "console")
    return {"console": ConsoleSMSProvider, "kavenegar": KavenegarSMSProvider}[name]()
