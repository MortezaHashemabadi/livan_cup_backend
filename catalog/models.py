from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_accessory = models.BooleanField(default=False)  # True برای هولدر/جعبه/درب
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Attribute(models.Model):
    name = models.CharField(max_length=100)  # سایز، تعداد جداره، نوع سطح، تکسچر
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)  # "8oz"، "2 جداره"، "گلاسه"، "کرکره‌ای"

    class Meta:
        unique_together = ('attribute', 'value')

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class CategoryAttribute(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_attributes')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=True)
    allow_multiple_values = models.BooleanField(default=False)  # True برای سایزِ هولدر/جعبه/درب

    class Meta:
        unique_together = ('category', 'attribute')

    def __str__(self):
        return f"{self.category.name} - {self.attribute.name}"


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_designable = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class StockStatus(models.TextChoices):
    IN_STOCK = "in_stock", "موجود"
    OUT_OF_STOCK = "out_of_stock", "ناموجود"
    COMING_SOON = "coming_soon", "به‌زودی موجود می‌شود"




class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=64, unique=True)
    attribute_values = models.ManyToManyField(AttributeValue, related_name='variants', blank=True)
    stock_status = models.CharField(max_length=20, choices=StockStatus.choices, default=StockStatus.IN_STOCK)
    available_from = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    related_variants = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='related_to')
    is_designable = models.BooleanField(default=False)

    def __str__(self):
        values = ", ".join(
            value.value for value in self.attribute_values.all()
        )
        return f"{self.product.name} ({values})"

    def validate_attribute_combination(self, attribute_value_ids=None):
        ids = attribute_value_ids if attribute_value_ids is not None else list(
            self.attribute_values.values_list('id', flat=True)
        )
        values = AttributeValue.objects.filter(id__in=ids).select_related('attribute')
        grouped = {}
        for av in values:
            grouped.setdefault(av.attribute_id, []).append(av)
        for attribute_id, vals in grouped.items():
            cat_attr = CategoryAttribute.objects.filter(
                category=self.product.category, attribute_id=attribute_id
            ).first()
            if cat_attr and not cat_attr.allow_multiple_values and len(vals) > 1:
                raise ValidationError(
                    f"برای «{self.product.category.name}»، مشخصه‌ی «{vals[0].attribute.name}» فقط یک مقدار می‌تواند داشته باشد."
                )


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/%Y/%m/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    variants = models.ManyToManyField(
        ProductVariant,
        related_name='images',
        blank=True,
        help_text="اگه خالی بماند، این عکس به‌عنوان عکس پیش‌فرض/عمومی محصول استفاده می‌شود.",
    )

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).update(is_primary=False)

    def __str__(self):
        return f"{self.product.name} - {self.order}"