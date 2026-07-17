from django.contrib import admin, messages
from django.utils.html import mark_safe
from .models import Cart, CartItem, Order, OrderItem
from .services import create_order_from_cart


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    # ستون‌هایی که در لیست آیتم‌های سبد خرید نمایش داده می‌شوند
    list_display = ['id', 'cart', 'variant', 'quantity', 'print_file_preview', 'created_at']

    # فیلترهای کناری صفحه
    list_filter = ['created_at']

    # قابلیت جستجو (بر اساس شماره تماس کاربرِ سبد و یا نام/SKU محصول)
    # فرض بر این است که variant فیلدی به نام sku دارد، اگر ندارد آن را تغییر دهید
    search_fields = ['cart__user__phone', 'variant__sku']

    # فیلدهایی که فقط خواندنی هستند
    readonly_fields = ['print_file_preview']

    # تابع نمایش عکس در صفحه لیست و جزئیات
    def print_file_preview(self, obj):
        if obj.print_file:
            return mark_safe(
                f'<a href="{obj.print_file.url}" target="_blank">'
                f'<img src="{obj.print_file.url}" style="max-height:80px; border-radius:4px"/>'
                f'</a>'
            )
        return "—"

    print_file_preview.short_description = "پیش‌نمایش فایل"

# ── میکسین مشترک برای preview (یه بار نوشته می‌شه، هر دو جا استفاده می‌شه) ──
class OrderItemPreviewMixin:
    def print_file_preview(self, obj):
        if obj.print_file:
            return mark_safe(
                f'<a href="{obj.print_file.url}" target="_blank">'
                f'<img src="{obj.print_file.url}" style="max-height:150px; border-radius:4px"/>'
                f'</a>'
            )
        return "فایلی آپلود نشده"
    print_file_preview.short_description = "فایل چاپ"

    def print_file_download(self, obj):
        if obj.print_file:
            return mark_safe(f'<a href="{obj.print_file.url}" download target="_blank">دانلود</a>')
        return "—"
    print_file_download.short_description = "دانلود فایل"

    def design_thumbnail_preview(self, obj):
        if obj.design and obj.design.thumbnail:
            return mark_safe(
                f'<a href="{obj.design.thumbnail.url}" target="_blank">'
                f'<img src="{obj.design.thumbnail.url}" style="max-height:150px; border-radius:4px"/>'
                f'</a>'
            )
        return "—"
    design_thumbnail_preview.short_description = "پیش‌نمایش طراحی"


# ── Inline (برای استفاده داخل OrderAdmin) ──
class OrderItemInline(OrderItemPreviewMixin, admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = [
        'variant', 'design', 'quantity', 'unit_price', 'subtotal',
        'print_file_preview', 'print_file_download', 'design_thumbnail_preview',
    ]
    fields = readonly_fields
    can_delete = False


# ── Standalone (صفحه‌ی مستقل برای هر OrderItem) ──
@admin.register(OrderItem)
class OrderItemAdmin(OrderItemPreviewMixin, admin.ModelAdmin):
    list_display = ['id', 'order', 'variant', 'quantity', 'unit_price', 'subtotal', 'print_file_preview', 'design_thumbnail_preview']
    list_filter = ['order__status']
    search_fields = ['order__id', 'variant__sku']
    readonly_fields = [
        'order', 'variant', 'design', 'quantity', 'unit_price', 'subtotal',
        'print_file_preview', 'print_file_download', 'design_thumbnail_preview',
    ]


# ── Cart ──
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ['print_file_preview']

    def print_file_preview(self, obj):
        if obj.print_file:
            return mark_safe(f'<img src="{obj.print_file.url}" style="max-height:80px; border-radius:4px"/>')
        return "—"
    print_file_preview.short_description = "پیش‌نمایش فایل"


@admin.action(description="ساخت سفارش از سبد انتخاب‌شده (با آدرس پیش‌فرض کاربر)")
def make_order_from_cart(modeladmin, request, queryset):
    for cart in queryset:
        address = cart.user.addresses.filter(is_default=True).first() or cart.user.addresses.first()
        if not address:
            messages.error(request, f"کاربر {cart.user.phone} هیچ آدرسی ثبت نکرده است")
            continue
        try:
            order = create_order_from_cart(cart, address)
            messages.success(request, f"سفارش #{order.id} برای {cart.user.phone} ساخته شد")
        except ValueError as e:
            messages.error(request, f"{cart.user.phone}: {e}")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'discount', 'updated_at']
    inlines = [CartItemInline]
    actions = [make_order_from_cart]


# ── Order ──
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total', 'has_files', 'created_at']
    list_filter = ['status']
    readonly_fields = ['subtotal', 'discount_amount', 'total', 'address_snapshot']
    inlines = [OrderItemInline]  # ← الان کار می‌کنه

    def has_files(self, obj):
        has = obj.items.filter(print_file__isnull=False).exclude(print_file='').exists()
        return mark_safe('<span style="color:green">✔ دارد</span>' if has else '<span style="color:#ccc">—</span>')
    has_files.short_description = "فایل چاپ"