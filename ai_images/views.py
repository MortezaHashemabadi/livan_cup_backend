from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .serializers import GenerateImageRequestSerializer, GeneratedImageSerializer
from .services import generate_image, ImageGenerationError, QuotaExceededError
from .models import GeneratedImage, ImageGenerationQuota
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class GenerateImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = GenerateImageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logo_file = request.FILES.get('logo_file')
        reference_files = request.FILES.getlist('reference_files')

        try:
            image_url = generate_image(
                prompt=serializer.validated_data['prompt'],
                user=request.user,
                existing_image_urls=serializer.validated_data.get('existing_image_urls', []),
                logo_file=logo_file,
                reference_files=reference_files,
            )
        except QuotaExceededError as e:
            return Response({"detail": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except ImageGenerationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        instance = GeneratedImage.objects.filter(image__endswith=image_url.split('/')[-1]).first()
        if instance:
            instance.user = request.user
            instance.save(update_fields=['user'])

        quota = ImageGenerationQuota.get_or_reset(request.user)
        return Response({
            "url": request.build_absolute_uri(image_url),
            "quota": {
                "used": quota.used_count,
                "limit": ImageGenerationQuota.MONTHLY_LIMIT,
                "remaining": quota.remaining(),
            }
        })


class QuotaStatusView(APIView):
    """وضعیت کوتای ماه جاری — برای نمایش توی داشبورد کاربر"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        quota = ImageGenerationQuota.get_or_reset(request.user)
        return Response({
            "used": quota.used_count,
            "limit": ImageGenerationQuota.MONTHLY_LIMIT,
            "remaining": quota.remaining(),
        })


class GeneratedImageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        images = GeneratedImage.objects.filter(user=request.user)
        return Response(GeneratedImageSerializer(images, many=True, context={'request': request}).data)