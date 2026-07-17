from django.contrib import admin
from .models import Discount


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'discount_type', 'value', 'is_active', 'valid_from', 'valid_to']
    filter_horizontal = ['categories', 'products']