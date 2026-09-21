from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ProductVariantViewSet, ProductCardViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('products', ProductViewSet)
router.register('variants', ProductVariantViewSet)

router.register('product-cards', ProductCardViewSet, basename='product-card')
urlpatterns = router.urls