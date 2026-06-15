from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OCRUploadView, OCRDocumentViewSet

router = DefaultRouter()
router.register(r'documents', OCRDocumentViewSet, basename='ocr-documents')

urlpatterns = [
    path('upload/', OCRUploadView.as_view(), name='ocr-upload'),
    path('review-queue/', OCRDocumentViewSet.as_view({'get': 'review_queue'}), name='ocr-review-queue'),
    path('', include(router.urls)),
]

