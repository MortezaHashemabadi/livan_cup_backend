from django.contrib import admin
from .models import Design


@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__phone']