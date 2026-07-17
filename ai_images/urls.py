from django.urls import path
from .views import GenerateImageView, GeneratedImageListView, QuotaStatusView

urlpatterns = [
    path('generate/', GenerateImageView.as_view()),
    path('history/', GeneratedImageListView.as_view()),
    path('quota/', QuotaStatusView.as_view()),
]