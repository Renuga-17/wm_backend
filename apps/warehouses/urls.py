from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WarehouseViewSet, RackViewSet, SpatialEntityViewSet,
    NavigationNodeViewSet, WarehousePathViewSet, RackCoordinateViewSet
)

router = DefaultRouter()
router.register(r'racks', RackViewSet, basename='racks')
router.register(r'spatial-entities', SpatialEntityViewSet, basename='spatial-entities')
router.register(r'navigation-nodes', NavigationNodeViewSet, basename='navigation-nodes')
router.register(r'paths', WarehousePathViewSet, basename='paths')
router.register(r'rack-coordinates', RackCoordinateViewSet, basename='rack-coordinates')
router.register(r'', WarehouseViewSet, basename='warehouses')

urlpatterns = [
    path('', include(router.urls)),
]


