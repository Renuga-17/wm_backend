from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OCRExtractView, OCRHistoryViewSet

router = DefaultRouter()
router.register(r'history', OCRHistoryViewSet, basename='ocr-history')

urlpatterns = [
    path('extract/', OCRExtractView.as_view(), name='ocr-extract'),
    path('', include(router.urls)),
]
