from rest_framework import permissions, mixins, viewsets
from .models import ProductReview, Testimonial
from .serializers import ProductReviewSerializer, TestimonialSerializer


class ProductReviewViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ProductReviewSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = ProductReview.objects.filter(is_approved=True).select_related('user')
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_approved=False)


class TestimonialViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Testimonial.objects.filter(is_featured=True)