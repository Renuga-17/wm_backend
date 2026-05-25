from rest_framework import viewsets
from .models import Warehouse, Rack, SpatialEntity, NavigationNode, WarehousePath, RackCoordinate
from .serializers import (
    WarehouseSerializer, RackSerializer, SpatialEntitySerializer,
    NavigationNodeSerializer, WarehousePathSerializer, RackCoordinateSerializer
)

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by('id')
    serializer_class = WarehouseSerializer

class RackViewSet(viewsets.ModelViewSet):
    queryset = Rack.objects.all().order_by('id')
    serializer_class = RackSerializer

class SpatialEntityViewSet(viewsets.ModelViewSet):
    queryset = SpatialEntity.objects.all().order_by('id')
    serializer_class = SpatialEntitySerializer

class NavigationNodeViewSet(viewsets.ModelViewSet):
    queryset = NavigationNode.objects.all().order_by('id')
    serializer_class = NavigationNodeSerializer

class WarehousePathViewSet(viewsets.ModelViewSet):
    queryset = WarehousePath.objects.all().order_by('id')
    serializer_class = WarehousePathSerializer

class RackCoordinateViewSet(viewsets.ModelViewSet):
    queryset = RackCoordinate.objects.all().order_by('id')
    serializer_class = RackCoordinateSerializer


