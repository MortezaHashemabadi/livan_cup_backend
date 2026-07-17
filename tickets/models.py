from django.db import models
from django.conf import settings


class TicketType(models.TextChoices):
    ORDER = 'order', 'مشکل سفارش'
    PRODUCT = 'product', 'سوال محصول'
    PAYMENT = 'payment', 'مشکل پرداخت'
    DESIGN = 'design', 'طراحی و چاپ'
    OTHER = 'other', 'سایر'


class TicketStatus(models.TextChoices):
    OPEN = 'open', 'باز'
    IN_REVIEW = 'in_review', 'در حال بررسی'
    ANSWERED = 'answered', 'پاسخ داده شده'
    CLOSED = 'closed', 'بسته شده'


class Ticket(models.Model):
    # کاربر لاگین‌کرده یا مهمان
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tickets'
    )
    # فیلدهای مهمان (اگه لاگین نکرده باشه اجباریه)
    fullname = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)

    ticket_type = models.CharField(max_length=20, choices=TicketType.choices, default=TicketType.OTHER)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    is_read = models.BooleanField(default=False)  # ادمین خونده یا نه
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.pk} - {self.subject} ({self.get_status_display()})"


class TicketReply(models.Model):
    """پاسخ ادمین به تیکت — فعلاً ساده، قابل گسترش"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='replies')
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ticket_replies'
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"پاسخ به تیکت #{self.ticket.pk}"