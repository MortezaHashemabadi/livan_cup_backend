import traceback

from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Design
from .serializers import DesignSerializer, AIImageGenerationSerializer
from .services import generate_base44_image


class DesignViewSet(viewsets.ModelViewSet):
    serializer_class = DesignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Design.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GenerateCupDesignView(APIView):
    permission_classes = [IsAuthenticated]  # چون مدل Design به User وصله، کاربر باید لاگین باشه

    def post(self, request):
        try:
            # ۱. پرینت کردن دیتایی که از فرانت‌اند می‌آید
            print("=== [DEBUG: Incoming Request Data] ===")
            print(request.data)
            serializer = AIImageGenerationSerializer(data=request.data)

            if serializer.is_valid():
                prompt = serializer.validated_data['prompt']
                size = serializer.validated_data['size']

                try:
                    # فراخوانی سرویس هوش مصنوعی
                    image_url = generate_base44_image(prompt=prompt, size=size)
                    return Response({'url': image_url}, status=status.HTTP_200_OK)

                except Exception as e:
                    # هندل کردن خطاهای ارتباط با Base44
                    return Response(
                        {'error': 'Failed to generate image from AI service.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("\n=== [ERROR 500 in GenerateCupDesignView] ===")
            print("Type of Error:", type(e).__name__)
            print("Error Message:", str(e))
            print("--- Full Traceback ---")
            traceback.print_exc()
            print("==============================================\n")

            return Response(
                {
                    "error": str(e),
                    "detail": "خطای سرور هنگام ارتباط با هوش مصنوعی"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
