from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Product, ProductVariant
from .serializers import CategorySerializer, ProductSerializer, ProductVariantSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = (
        Product.objects.filter(is_active=True)
        .select_related('category')
        .prefetch_related('variants__attribute_values__attribute', 'variants__price_tiers')
    )
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        qs = super().get_queryset()
        category_slug = self.request.query_params.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs


class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = ProductVariant.objects.filter(is_active=True)
    serializer_class = ProductVariantSerializer

    @action(detail=True, methods=['get'])
    def compatible_accessories(self, request, pk=None):
        """با گرفتن یه Variant لیوان، هولدر/جعبه/دربِ هم‌سایزش رو برمی‌گردونه"""
        variant = self.get_object()
        size_values = variant.attribute_values.filter(attribute__slug='size')
        accessories = ProductVariant.objects.filter(
            attribute_values__in=size_values,
            product__category__is_accessory=True,
            is_active=True,
        ).distinct()
        return Response(ProductVariantSerializer(accessories, many=True).data)