from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from catalog.models import ProductVariant
from designs.models import Design
from accounts.models import Address
from pricing.models import Discount


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    discount = models.ForeignKey(Discount, null=True, blank=True, on_delete=models.SET_NULL, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"سبد {self.user.phone}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    design = models.ForeignKey(Design, null=True, blank=True, on_delete=models.SET_NULL, related_name='cart_items')
    print_file = models.ImageField(
        upload_to='cart_print_files/%Y/%m/', null=True, blank=True,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'webp', 'svg'])],
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'در انتظار پرداخت'
    PAID = 'paid', 'پرداخت شده'
    PROCESSING = 'processing', 'در حال پردازش'
    SHIPPED = 'shipped', 'ارسال شده'
    DELIVERED = 'delivered', 'تحویل شده'
    CANCELLED = 'cancelled', 'لغو شده'


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='orders')
    notes = models.TextField(blank=True)
    address_snapshot = models.TextField()
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    discount = models.ForeignKey(Discount, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)
    total = models.DecimalField(max_digits=12, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"سفارش #{self.pk} - {self.user.phone}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name='order_items')
    design = models.ForeignKey(Design, null=True, blank=True, on_delete=models.SET_NULL, related_name='order_items')
    print_file = models.ImageField(upload_to='order_print_files/%Y/%m/', null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)