from django.db.models import Q
from .models import DiscountType


def get_unit_price(variant, quantity):
    tier = (
        variant.price_tiers
        .filter(min_quantity__lte=quantity)
        .filter(Q(max_quantity__gte=quantity) | Q(max_quantity__isnull=True))
        .order_by('-min_quantity')
        .first()
    )
    return tier.unit_price if tier else None


def validate_discount(discount, subtotal):
    if not discount.is_valid():
        raise ValueError("این کد تخفیف معتبر نیست یا منقضی شده است")
    if discount.min_order_amount and subtotal < discount.min_order_amount:
        raise ValueError(f"حداقل مبلغ سفارش برای این تخفیف {discount.min_order_amount} تومان است")


def calculate_discount_amount(discount, subtotal):
    if discount.discount_type == DiscountType.PERCENTAGE:
        return min(subtotal * discount.value / 100, subtotal)
    return min(discount.value, subtotal)