from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .product_views import ProductDimensionViewSet, ProductStorageRuleViewSet

router = DefaultRouter()
router.register(r'storage-rules', ProductStorageRuleViewSet, basename='product-storage-rules')
router.register(r'', ProductDimensionViewSet, basename='product-dimensions')

urlpatterns = [
    path('', include(router.urls)),
]
