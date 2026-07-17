from rest_framework import serializers
from .models import Category, AttributeValue, Product, ProductVariant, ProductImage
from pricing.serializers import PriceTierSerializer


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute = serializers.CharField(source='attribute.name')
    attribute_slug = serializers.CharField(source='attribute.slug')

    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute', 'attribute_slug', 'value']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']


def _resolve_variant_images(variant):
    images = variant.images.all()
    if not images.exists():
        images = variant.product.images.filter(variants__isnull=True)
    return images


class RelatedVariantSerializer(serializers.ModelSerializer):
    """نسخه‌ی سبک، فقط برای نمایش داخل لیست related_variants (جلوگیری از رفرنس حلقه‌ای)"""
    attribute_values = AttributeValueSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name')
    product_slug = serializers.CharField(source='product.slug')
    price_tiers = PriceTierSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'attribute_values', 'stock_status', 'images', 'product_name', 'product_slug', 'price_tiers']

    def get_images(self, obj):
        return ProductImageSerializer(_resolve_variant_images(obj), many=True).data


class ProductVariantSerializer(serializers.ModelSerializer):
    attribute_values = AttributeValueSerializer(many=True, read_only=True)
    price_tiers = PriceTierSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()
    related_variants = RelatedVariantSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'attribute_values', 'stock_status', 'available_from',
            'price_tiers', 'images', 'related_variants','created_at','is_designable'
        ]

    def get_images(self, obj):
        return ProductImageSerializer(_resolve_variant_images(obj), many=True).data


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.CharField(source='category.name')
    category_slug = serializers.CharField(source='category.slug')

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category', 'category_slug', 'variants', 'images', 'is_designable']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'is_accessory', 'description', 'image']