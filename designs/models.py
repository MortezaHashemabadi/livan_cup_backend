from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings


class Design(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='designs')
    name = models.CharField(max_length=255, blank=True)
    design_data = models.JSONField()  # خروجی stage.toJSON() از Konva
    thumbnail = models.ImageField(
        upload_to='designs/thumbnails/%Y/%m/',
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'webp'])],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name or f"Design #{self.pk} ({self.user.phone})"