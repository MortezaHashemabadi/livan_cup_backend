import factory
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, OTP, OTPPurpose, Address, BusinessProfile


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    phone = factory.Sequence(lambda n: f"091{n:08d}")
    first_name = "تست"
    last_name = "کاربر"
    is_phone_verified = True


class OTPFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OTP

    phone = "09123456789"
    code = "123456"
    purpose = OTPPurpose.LOGIN
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=2))


class AddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Address

    user = factory.SubFactory(UserFactory)
    title = "دفتر مرکزی"
    province = "تهران"
    city = "تهران"
    full_address = "خیابان آزادی"
    postal_code = "1234567890"