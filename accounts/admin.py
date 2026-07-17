from django.contrib import admin
from .models import User, OTP, BusinessProfile, Address

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["phone", "first_name", "last_name", "is_phone_verified", "is_active", "date_joined"]
    search_fields = ["phone", "first_name", "last_name"]

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ["phone", "code", "purpose", "is_used", "created_at", "expires_at"]

admin.site.register(BusinessProfile)
admin.site.register(Address)