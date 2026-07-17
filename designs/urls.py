from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DesignViewSet, GenerateCupDesignView

# رجیستر کردن ViewSetها در روتر
router = DefaultRouter()
router.register('', DesignViewSet, basename='design')

# ترکیب path معمولی برای APIView با urlهای روتر
urlpatterns = [
    path('generate-design/', GenerateCupDesignView.as_view(), name='generate-design'),
    path('', include(router.urls)),
]