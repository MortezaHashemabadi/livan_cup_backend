from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from catalog.models import Product


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # هر کاربر فقط یک نظر برای هر محصول

    def clean(self):
        from cart_orders.models import OrderItem
        has_purchased = OrderItem.objects.filter(
            order__user=self.user, variant__product=self.product,
        ).exclude(order__status='cancelled').exists()
        if not has_purchased:
            raise ValidationError("فقط خریداران این محصول می‌توانند نظر ثبت کنند")

    def __str__(self):
        return f"{self.product.name} - {self.user.phone} ({self.rating}/5)"


class Testimonial(models.Model):
    customer_name = models.CharField(max_length=150)
    customer_title = models.CharField(max_length=150, blank=True)  # مثلا "صاحب کافه آرامیس"
    avatar = models.ImageField(upload_to='testimonials/%Y/%m/', null=True, blank=True)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True
    )
    comment = models.TextField()
    is_featured = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.customer_name