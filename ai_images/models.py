from django.db import models
from django.conf import settings
from django.utils import timezone


class GeneratedImage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='generated_images'
    )
    prompt = models.TextField()
    image = models.ImageField(upload_to='ai_generated/%Y/%m/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AI Image #{self.pk} — {self.prompt[:50]}"


class ImageGenerationQuota(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='image_quota'
    )
    used_count = models.PositiveSmallIntegerField(default=0)
    month = models.PositiveSmallIntegerField()  # عدد ماه: 1-12
    year = models.PositiveIntegerField()

    MONTHLY_LIMIT = 3

    class Meta:
        unique_together = ('user', 'month', 'year')

    def __str__(self):
        return f"{self.user.phone} — {self.year}/{self.month} ({self.used_count}/{self.MONTHLY_LIMIT})"

    @classmethod
    def get_or_reset(cls, user):

        now = timezone.now()
        quota, created = cls.objects.get_or_create(
            user=user,
            month=now.month,
            year=now.year,
            defaults={'used_count': 0},
        )
        return quota

    def has_remaining(self):
        return self.used_count < self.MONTHLY_LIMIT

    def remaining(self):
        return max(0, self.MONTHLY_LIMIT - self.used_count)

    def increment(self):
        self.used_count += 1
        self.save(update_fields=['used_count'])