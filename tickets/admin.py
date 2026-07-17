from django.contrib import admin
from .models import Ticket, TicketReply


class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1
    readonly_fields = ['created_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'fullname', 'phone', 'ticket_type', 'status', 'is_read', 'created_at']
    list_filter = ['status', 'ticket_type', 'is_read']
    search_fields = ['fullname', 'phone', 'subject']
    readonly_fields = ['user', 'fullname', 'phone', 'ticket_type', 'subject', 'message', 'created_at']
    inlines = [TicketReplyInline]
    actions = ['mark_as_read', 'mark_as_closed']

    @admin.action(description="علامت‌گذاری به‌عنوان خوانده‌شده")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="بستن تیکت‌های انتخاب‌شده")
    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')