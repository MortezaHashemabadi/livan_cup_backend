from django.db import models


class GalleryImage(models.Model):
    image = models.ImageField(upload_to='gallery/%Y/%m/')
    title = models.CharField(max_length=255, blank=True)
    tag = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f"Gallery #{self.pk}"