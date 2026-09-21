from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Product, ProductVariant, ProductCard
from .serializers import CategorySerializer, ProductSerializer, ProductVariantSerializer, ProductCardSerializer


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

    @action(detail=True, methods=['get'], url_path='listed-variants')
    def listed_variants(self, request, slug=None):
        """فقط واریانت‌هایی که is_listed=True دارن — برای صفحه‌ی لیست محصولات"""
        product = self.get_object()
        variants = product.variants.filter(is_active=True, is_listed=True)
        return Response(ProductVariantSerializer(variants, many=True).data)

    def get_queryset(self):
        qs = super().get_queryset()
        category_slug = self.request.query_params.get('category')
        if category_slug:
            from .models import Category
            # پیدا کردن کتگوری انتخابی
            try:
                category = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                return qs.none()

            # جمع‌آوری ID خودش + همه‌ی زیرمجموعه‌هاش (یه سطح)
            category_ids = [category.id]
            children_ids = list(
                Category.objects.filter(parent=category).values_list('id', flat=True)
            )
            category_ids.extend(children_ids)

            qs = qs.filter(category_id__in=category_ids)
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

    @action(detail=False, methods=['get'], url_path='top-selling')
    def top_selling(self, request):
        variants = (
            ProductVariant.objects.filter(is_active=True, sales_count__gt=0)
            .select_related('product')  # ← مهمه
            .order_by('-sales_count')[:10]
        )
        return Response(ProductVariantSerializer(variants, many=True).data)

class ProductCardViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductCardSerializer
        return ProductSerializer

    def get_queryset(self):
        if self.action == 'list':
            return ProductCard.objects.filter(is_active=True)
        return (
            Product.objects.filter(is_active=True)
            .select_related('category')
            .prefetch_related(
                'images',
                'variants__price_tiers',
                'variants__attribute_values__attribute',
                'variants__option_groups__choices',
                'variants__related_variants__attribute_values__attribute',
                'variants__related_variants__images',
            )
        )

    def list(self, request, *args, **kwargs):
        qs = ProductCard.objects.filter(is_active=True)

        category_slug = request.query_params.get('category')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                category_ids = [category.id] + list(
                    Category.objects.filter(parent=category).values_list('id', flat=True)
                )
                qs = qs.filter(category_id__in=category_ids)
            except Category.DoesNotExist:
                qs = qs.none()

        for key, value in request.query_params.items():
            if key in ('category', 'ordering'):
                continue
            qs = qs.filter(filter_data__contains={key: value})

        ordering = request.query_params.get('ordering')
        if ordering == 'price_asc':
            qs = qs.order_by('price_from')
        elif ordering == 'price_desc':
            qs = qs.order_by('-price_from')
        else:
            qs = qs.order_by('order')

        serializer = ProductCardSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)