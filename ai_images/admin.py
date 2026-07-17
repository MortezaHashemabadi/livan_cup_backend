from django.contrib import admin
from django.utils.html import mark_safe
from .models import GeneratedImage, ImageGenerationQuota


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'prompt_short', 'preview', 'created_at']
    readonly_fields = ['user', 'prompt', 'preview', 'created_at']

    def prompt_short(self, obj):
        return obj.prompt[:60] + "..." if len(obj.prompt) > 60 else obj.prompt
    prompt_short.short_description = "پرامپت"

    def preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height:120px; border-radius:4px"/>')
        return "—"
    preview.short_description = "پیش‌نمایش"


@admin.register(ImageGenerationQuota)
class ImageGenerationQuotaAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'month', 'used_count', 'remaining_display']
    list_filter = ['year', 'month']
    search_fields = ['user__phone']
    readonly_fields = ['user', 'month', 'year', 'used_count']
    actions = ['reset_quota']

    def remaining_display(self, obj):
        remaining = obj.remaining()
        color = 'green' if remaining > 0 else 'red'
        return mark_safe(f'<span style="color:{color}">{remaining} از {obj.MONTHLY_LIMIT}</span>')
    remaining_display.short_description = "باقی‌مانده"

    @admin.action(description="ریست کوتا برای کاربران انتخاب‌شده")
    def reset_quota(self, request, queryset):
        queryset.update(used_count=0)