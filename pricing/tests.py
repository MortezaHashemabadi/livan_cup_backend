import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

from catalog.models import Category, Product, ProductVariant
from .models import PriceTier, Discount, DiscountType


@pytest.fixture
def sample_variant(db):
    category = Category.objects.create(name="لیوان کاغذی")
    product = Product.objects.create(category=category, name="لیوان تست")
    return ProductVariant.objects.create(product=product, sku="TEST-SKU-1")


@pytest.mark.django_db
def test_price_tiers_ordered_by_min_quantity(sample_variant):
    PriceTier.objects.create(variant=sample_variant, min_quantity=100, max_quantity=499, unit_price=1500)
    PriceTier.objects.create(variant=sample_variant, min_quantity=1, max_quantity=99, unit_price=2000)
    PriceTier.objects.create(variant=sample_variant, min_quantity=500, max_quantity=None, unit_price=1200)

    tiers = list(sample_variant.price_tiers.all())
    assert [t.min_quantity for t in tiers] == [1, 100, 500]


@pytest.mark.django_db
def test_price_tier_clean_raises_when_max_lte_min(sample_variant):
    tier = PriceTier(variant=sample_variant, min_quantity=100, max_quantity=50, unit_price=1000)
    with pytest.raises(ValidationError):
        tier.clean()


@pytest.mark.django_db
def test_discount_is_valid_within_date_range():
    discount = Discount.objects.create(
        name="تخفیف تست", discount_type=DiscountType.PERCENTAGE, value=10,
        valid_from=timezone.now() - timedelta(days=1),
        valid_to=timezone.now() + timedelta(days=1),
    )
    assert discount.is_valid() is True


@pytest.mark.django_db
def test_discount_invalid_when_expired():
    discount = Discount.objects.create(
        name="تخفیف منقضی", discount_type=DiscountType.FIXED, value=5000,
        valid_from=timezone.now() - timedelta(days=10),
        valid_to=timezone.now() - timedelta(days=1),
    )
    assert discount.is_valid() is False


@pytest.mark.django_db
def test_discount_invalid_when_usage_limit_reached():
    discount = Discount.objects.create(
        name="تخفیف محدود", discount_type=DiscountType.PERCENTAGE, value=15,
        valid_from=timezone.now() - timedelta(days=1),
        valid_to=timezone.now() + timedelta(days=1),
        usage_limit=1, used_count=1,
    )
    assert discount.is_valid() is False


@pytest.mark.django_db
def test_discount_invalid_when_inactive():
    discount = Discount.objects.create(
        name="تخفیف غیرفعال", discount_type=DiscountType.PERCENTAGE, value=15,
        valid_from=timezone.now() - timedelta(days=1),
        valid_to=timezone.now() + timedelta(days=1),
        is_active=False,
    )
    assert discount.is_valid() is False