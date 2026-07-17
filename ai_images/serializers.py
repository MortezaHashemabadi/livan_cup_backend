from rest_framework import serializers
from .models import GeneratedImage


class GenerateImageRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=1000, min_length=3)
    existing_image_urls = serializers.ListField(
        child=serializers.URLField(), required=False, default=list
    )
    reference_image = serializers.ImageField(required=False)

    def validate(self, attrs):
        return attrs

class GeneratedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedImage
        fields = ['id', 'prompt', 'image', 'created_at']