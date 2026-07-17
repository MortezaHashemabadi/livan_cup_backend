from rest_framework.routers import DefaultRouter
from .views import ProductReviewViewSet, TestimonialViewSet

router = DefaultRouter()
router.register('product-reviews', ProductReviewViewSet, basename='product-review')
router.register('testimonials', TestimonialViewSet, basename='testimonial')

urlpatterns = router.urls