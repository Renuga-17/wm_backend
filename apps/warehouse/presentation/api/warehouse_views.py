from rest_framework import viewsets
from apps.warehouse.infrastructure.persistence.models import Warehouse, Rack, SpatialEntity, NavigationNode, WarehousePath, RackCoordinate
from .serializers import (
    WarehouseSerializer, RackSerializer, SpatialEntitySerializer,
    NavigationNodeSerializer, WarehousePathSerializer, RackCoordinateSerializer
)
from common.permissions import ReadOnlyOrAuthenticated


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by('id')
    serializer_class = WarehouseSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class RackViewSet(viewsets.ModelViewSet):
    queryset = Rack.objects.all().order_by('id')
    serializer_class = RackSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class SpatialEntityViewSet(viewsets.ModelViewSet):
    queryset = SpatialEntity.objects.all().order_by('id')
    serializer_class = SpatialEntitySerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class NavigationNodeViewSet(viewsets.ModelViewSet):
    queryset = NavigationNode.objects.all().order_by('id')
    serializer_class = NavigationNodeSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class WarehousePathViewSet(viewsets.ModelViewSet):
    queryset = WarehousePath.objects.all().order_by('id')
    serializer_class = WarehousePathSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class RackCoordinateViewSet(viewsets.ModelViewSet):
    queryset = RackCoordinate.objects.all().order_by('id')
    serializer_class = RackCoordinateSerializer
    permission_classes = [ReadOnlyOrAuthenticated]
