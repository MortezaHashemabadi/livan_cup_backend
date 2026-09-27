# catalog/management/commands/add_bag_options.py

from django.core.management.base import BaseCommand
from catalog.models import ProductVariant, VariantOptionGroup, VariantOptionChoice


HANDLE_PRICES = {
    '40': 1800,
    '60': 1800,
    '90': 2700,
}

PRINT_COLORS = [
    ('معمولی', 4500, True),
    ('نقره‌ای', 5000, False),
    ('فسفری', 5500, False),
    ('طلایی', 5800, False),
    ('سفید', 6000, False),
]

COLOR_COUNT = [
    ('تک رنگ', 0, True),
    ('دو رنگ', 4000, False),
]


class Command(BaseCommand):
    help = "اضافه کردن option groups به همه‌ی واریانت‌های بگ"

    def handle(self, *args, **kwargs):
        bag_variants = ProductVariant.objects.filter(
            product__category__name__icontains='بگ'
        ).prefetch_related('attribute_values__attribute')

        self.stdout.write(f"{bag_variants.count()} واریانت بگ پیدا شد")

        for variant in bag_variants:
            # پیدا کردن گرماژ از attribute_values
            weight = None
            for av in variant.attribute_values.all():
                if av.attribute.name == 'گرماژ':
                    weight = av.value.replace('گرم', '').strip()
                    break

            self.stdout.write(f"  → {variant.sku} (گرماژ: {weight})")

            # ── گروه ۱: نوع دستگیره ──
            handle_group, _ = VariantOptionGroup.objects.get_or_create(
                variant=variant,
                name='نوع دستگیره',
                defaults={'is_required': True, 'order': 0}
            )
            VariantOptionChoice.objects.get_or_create(
                group=handle_group, name='پانچ',
                defaults={'price_modifier': 0, 'is_default': True, 'order': 0}
            )
            handle_price = HANDLE_PRICES.get(weight, 1800)
            VariantOptionChoice.objects.get_or_create(
                group=handle_group, name='زنبیلی',
                defaults={'price_modifier': handle_price, 'is_default': False, 'order': 1}
            )

            # ── گروه ۲: رنگ چاپ ──
            color_group, _ = VariantOptionGroup.objects.get_or_create(
                variant=variant,
                name='رنگ چاپ',
                defaults={'is_required': True, 'order': 2}
            )
            for i, (name, price, is_default) in enumerate(PRINT_COLORS):
                VariantOptionChoice.objects.get_or_create(
                    group=color_group, name=name,
                    defaults={'price_modifier': price, 'is_default': is_default, 'order': i}
                )

            # ── گروه ۳: تعداد رنگ ──
            count_group, _ = VariantOptionGroup.objects.get_or_create(
                variant=variant,
                name='تعداد رنگ',
                defaults={'is_required': True, 'order': 1}
            )
            for i, (name, price, is_default) in enumerate(COLOR_COUNT):
                VariantOptionChoice.objects.get_or_create(
                    group=count_group, name=name,
                    defaults={'price_modifier': price, 'is_default': is_default, 'order': i}
                )

        self.stdout.write(self.style.SUCCESS("✅ تموم شد"))