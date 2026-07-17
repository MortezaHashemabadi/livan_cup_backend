from rest_framework import mixins, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import GalleryImage
from .serializers import GalleryImageSerializer, GalleryImageCreateSerializer

class GalleryImageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = GalleryImageSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = GalleryImage.objects.filter(is_featured=True)
        tag = self.request.query_params.get('tag')
        if tag:
            qs = qs.filter(tag=tag)
        return qs


class GalleryImageCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        print("FILES:", request.FILES)
        print("DATA:", request.data)
        serializer = GalleryImageCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(seen=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print("ERRORS:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)