from django import forms
from django.contrib import admin
from .models import Category, Attribute, AttributeValue, CategoryAttribute, Product, ProductVariant, ProductImage, \
    VariantOptionChoice, VariantOptionGroup, ProductCard
from pricing.models import PriceTier


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    inlines = [AttributeValueInline]


class CategoryAttributeInline(admin.TabularInline):
    model = CategoryAttribute
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_accessory', 'is_active']
    inlines = [CategoryAttributeInline]
    fields = ['name', 'slug', 'parent', 'is_accessory', 'is_active', 'description', 'image', 'price_table_axes']


class ProductVariantAdminForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = '__all__'

    def clean_attribute_values(self):
        values = self.cleaned_data['attribute_values']
        if self.instance.product_id:
            self.instance.validate_attribute_combination(attribute_value_ids=[v.id for v in values])
        return values


class PriceTierInline(admin.TabularInline):
    model = PriceTier
    extra = 1


# @admin.register(ProductVariant)
# class ProductVariantAdmin(admin.ModelAdmin):
#     form = ProductVariantAdminForm
#
#     list_display = [
#         'sku',
#         'display_attribute_values',
#         'product',
#         'stock_status',
#         'available_from'
#     ]
#
#     filter_horizontal = ['attribute_values', 'related_variants']
#     inlines = [PriceTierInline]
#
#     @admin.display(description="Attributes")
#     def display_attribute_values(self, obj):
#         return ", ".join(
#             value.value for value in obj.attribute_values.all()
#         )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']  # variants رو از صفحه‌ی جدا مدیریت می‌کنیم

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = [
        'display_variants',
        'product',
        'is_primary',
        'order'
    ]
    list_filter = ['product']
    filter_horizontal = ['variants']

    @admin.display(description="Variants")
    def display_variants(self, obj):
        variants = []
        for variant in obj.variants.all():
            attrs = ", ".join(
                av.value for av in variant.attribute_values.all()
            )
            variants.append(attrs)

        return " | ".join(variants)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active']
    inlines = [ProductImageInline]
    fields = ['name', 'slug', 'category', 'description', 'features', 'is_active']

class VariantOptionChoiceInline(admin.TabularInline):
    model = VariantOptionChoice
    extra = 1


class VariantOptionGroupInline(admin.StackedInline):
    model = VariantOptionGroup
    extra = 1
    inlines = [VariantOptionChoiceInline]  # جنگو nested inline نداره، جدا ثبت می‌کنیم


@admin.register(VariantOptionGroup)
class VariantOptionGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'variant', 'is_required', 'order']
    inlines = [VariantOptionChoiceInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    form = ProductVariantAdminForm
    list_display = ['id','sku', 'product', 'stock_status','sales_count', 'is_active']
    filter_horizontal = ['attribute_values', 'related_variants']
    inlines = [PriceTierInline, VariantOptionGroupInline]
    search_fields = ['sku']


@admin.register(ProductCard)
class ProductCardAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price_from', 'price_to', 'is_active', 'order']
    list_editable = ['is_active', 'order']