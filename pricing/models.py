from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from catalog.models import ProductVariant, Category, Product


class PriceTier(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='price_tiers')
    min_quantity = models.PositiveIntegerField()
    max_quantity = models.PositiveIntegerField(null=True, blank=True)  # خالی = به بالا (∞)
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)  # تومان

    class Meta:
        ordering = ['min_quantity']

    def clean(self):
        if self.max_quantity is not None and self.max_quantity <= self.min_quantity:
            raise ValidationError("max_quantity باید بزرگتر از min_quantity باشد")

    def __str__(self):
        upper = self.max_quantity or "∞"
        return f"{self.variant.sku}: {self.min_quantity}-{upper} → {self.unit_price}"


class DiscountType(models.TextChoices):
    PERCENTAGE = "percentage", "درصدی"
    FIXED = "fixed", "مقدار ثابت"


class Discount(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, null=True, blank=True)  # خالی = بدون کد، اتومات
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
    value = models.DecimalField(max_digits=10, decimal_places=0)
    min_order_amount = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    categories = models.ManyToManyField(Category, blank=True, related_name='discounts')
    products = models.ManyToManyField(Product, blank=True, related_name='discounts')
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        now = timezone.now()
        if not self.is_active or now < self.valid_from or now > self.valid_to:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        return True

    def __str__(self):
        return self.name