from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GalleryImageViewSet, GalleryImageCreateView

router = DefaultRouter()
router.register('', GalleryImageViewSet, basename='gallery')

urlpatterns = [
    path('submit/', GalleryImageCreateView.as_view()),
    path('', include(router.urls)),

]
