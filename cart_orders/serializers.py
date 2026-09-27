from rest_framework import serializers
from catalog.models import StockStatus
from .models import CartItem, Cart, Order, OrderItem
from pricing.services import get_unit_price
from catalog.serializers import ProductVariantSerializer
from pricing.models import DiscountType

from catalog.models import VariantOptionChoice, VariantOptionGroup

class CartItemSerializer(serializers.ModelSerializer):
    unit_price = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    variant_detail = ProductVariantSerializer(source='variant', read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    product_slug = serializers.CharField(source='variant.product.slug', read_only=True)
    selected_option_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, default=list
    )

    class Meta:
        model = CartItem
        fields = [
            'id', 'variant', 'variant_detail', 'product_name', 'product_slug',
            'design', 'print_file', 'quantity', 'unit_price', 'subtotal',
            'selected_options', 'selected_option_ids','fabric_color','print_color',
        ]
        read_only_fields = ['selected_options']

    def get_unit_price(self, obj):
        choice_ids = [opt['choice_id'] for opt in obj.selected_options]
        return get_unit_price(obj.variant, obj.quantity, choice_ids)

    def get_subtotal(self, obj):
        price = self.get_unit_price(obj)
        return price * obj.quantity if price is not None else None

    def validate(self, attrs):
        variant = attrs.get('variant')
        choice_ids = attrs.pop('selected_option_ids', [])

        if variant and choice_ids:
            attrs['selected_options'] = _validate_and_snapshot_options(variant, choice_ids)
        else:
            attrs['selected_options'] = []

        # چک required groups
        if variant:
            required_groups = variant.option_groups.filter(is_required=True)
            selected_group_ids = {
                opt['group_id'] for opt in attrs.get('selected_options', [])
            }
            for group in required_groups:
                if group.id not in selected_group_ids:
                    raise serializers.ValidationError(
                        f"انتخاب گزینه‌ای برای «{group.name}» الزامی است"
                    )
        return attrs

    def validate_variant(self, value):
        if value.stock_status != StockStatus.IN_STOCK:
            raise serializers.ValidationError("این محصول در حال حاضر موجود نیست")
        return value

    def validate_design(self, value):
        request = self.context['request']
        if value and value.user_id != request.user.id:
            raise serializers.ValidationError("این طراحی متعلق به شما نیست")
        return value


def _validate_and_snapshot_options(variant, choice_ids):
    """آپشن‌های انتخابی رو اعتبارسنجی می‌کنه و snapshot کامل می‌سازه."""
    choices = VariantOptionChoice.objects.filter(
        id__in=choice_ids, group__variant=variant
    ).select_related('group')

    if len(choices) != len(choice_ids):
        raise serializers.ValidationError("یک یا چند آپشن انتخابی برای این محصول معتبر نیست")

    # فقط یه انتخاب از هر گروه مجازه
    seen_groups = {}
    for choice in choices:
        if choice.group_id in seen_groups:
            raise serializers.ValidationError(
                f"فقط یک گزینه از «{choice.group.name}» می‌توان انتخاب کرد"
            )
        seen_groups[choice.group_id] = True

    return [
        {
            "group_id": c.group_id,
            "group_name": c.group.name,
            "choice_id": c.id,
            "choice_name": c.name,
            "price_modifier": int(c.price_modifier),
        }
        for c in choices
    ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    discount_code = serializers.CharField(source='discount.code', read_only=True, default=None)
    discount_amount = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'subtotal', 'discount_code', 'discount_amount', 'total']

    def get_subtotal(self, obj):
        total = 0
        for item in obj.items.all():
            price = get_unit_price(item.variant, item.quantity)
            if price is not None:
                total += price * item.quantity
        return total

    def get_discount_amount(self, obj):
        from pricing.services import validate_discount, calculate_discount_amount
        if not obj.discount:
            return 0
        try:
            validate_discount(obj.discount, self.get_subtotal(obj))
        except ValueError:
            return 0
        return calculate_discount_amount(obj.discount, self.get_subtotal(obj))

    def get_total(self, obj):
        return self.get_subtotal(obj) - self.get_discount_amount(obj)


class OrderItemSerializer(serializers.ModelSerializer):
    variant_detail = ProductVariantSerializer(source='variant', read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    product_slug = serializers.CharField(source='variant.product.slug', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'variant', 'variant_detail', 'product_name', 'product_slug', 'design', 'print_file', 'quantity', 'unit_price', 'subtotal','fabric_color','print_color',]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    discount_code = serializers.CharField(source='discount.code', read_only=True, default=None)
    discount_percent = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'status', 'address', 'address_snapshot', 'notes', 'subtotal', 'discount_code', 'discount_amount', 'discount_percent', 'total', 'items', 'created_at']

    def get_discount_percent(self, obj):
        if not obj.discount or obj.discount.discount_type != DiscountType.PERCENTAGE:
            return None
        return float(obj.discount.value)