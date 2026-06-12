from rest_framework import viewsets
from apps.warehouse.infrastructure.persistence.models import Zone, ZoneBoundary, ZoneGroup, Aisle
from .serializers import ZoneSerializer, ZoneBoundarySerializer, ZoneGroupSerializer, AisleSerializer

class ZoneGroupViewSet(viewsets.ModelViewSet):
    queryset = ZoneGroup.objects.all().order_by('id')
    serializer_class = ZoneGroupSerializer

class AisleViewSet(viewsets.ModelViewSet):
    queryset = Aisle.objects.all().order_by('id')
    serializer_class = AisleSerializer
class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all().order_by('id')
    serializer_class = ZoneSerializer

class ZoneBoundaryViewSet(viewsets.ModelViewSet):
    queryset = ZoneBoundary.objects.all().order_by('id')
    serializer_class = ZoneBoundarySerializer


