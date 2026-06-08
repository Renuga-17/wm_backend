from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovementViewSet, StorageAllocationViewSet

router = DefaultRouter()
router.register(r'allocations', StorageAllocationViewSet, basename='storage-allocations')
router.register(r'', MovementViewSet, basename='movements')

urlpatterns = [
    path('', include(router.urls)),
]

