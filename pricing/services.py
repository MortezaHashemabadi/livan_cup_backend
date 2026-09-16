from django.db.models import Q, Sum
from .models import DiscountType
from catalog.models import VariantOptionChoice


def get_unit_price(variant, quantity, selected_choice_ids=None):
    """
    قیمت پایه از PriceTier + جمع price_modifier آپشن‌های انتخاب‌شده
    selected_choice_ids: لیست ID های VariantOptionChoice که کاربر انتخاب کرده
    """
    tier = (
        variant.price_tiers
        .filter(min_quantity__lte=quantity)
        .filter(Q(max_quantity__gte=quantity) | Q(max_quantity__isnull=True))
        .order_by('-min_quantity')
        .first()
    )
    if not tier:
        return None

    base_price = tier.unit_price

    if selected_choice_ids:
        modifier = (
            VariantOptionChoice.objects
            .filter(id__in=selected_choice_ids, group__variant=variant)
            .aggregate(total=Sum('price_modifier'))['total'] or 0
        )
        return base_price + modifier

    return base_price


def validate_discount(discount, subtotal):
    if not discount.is_valid():
        raise ValueError("این کد تخفیف معتبر یا منقضی شده است")
    if discount.min_order_amount and subtotal < discount.min_order_amount:
        raise ValueError(f"حداقل مبلغ سفارش برای این تخفیف {discount.min_order_amount} تومان است")


def calculate_discount_amount(discount, subtotal):
    if discount.discount_type == DiscountType.PERCENTAGE:
        return min(subtotal * discount.value / 100, subtotal)
    return min(discount.value, subtotal)