from rest_framework import serializers
from .models import Design


class DesignSerializer(serializers.ModelSerializer):
    design_data = serializers.JSONField(binary=True)  # برای parse شدن وقتی از multipart می‌آد

    class Meta:
        model = Design
        fields = ['id', 'name', 'design_data', 'thumbnail', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_thumbnail(self, value):
        max_size_mb = 5
        if value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(f"حجم تصویر نباید بیشتر از {max_size_mb} مگابایت باشد")
        return value

class AIImageGenerationSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True, allow_blank=False)
    size = serializers.ChoiceField(
        choices=['80', '120', '220', '330', '400'],
        required=True)