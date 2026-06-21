from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .classification_views import ProductClassificationViewSet

router = DefaultRouter()
router.register(r'', ProductClassificationViewSet, basename='product-classifications')

urlpatterns = [
    path('', include(router.urls)),
]
