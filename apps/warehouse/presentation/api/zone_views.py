from rest_framework import viewsets
from apps.warehouse.infrastructure.persistence.models import Zone, ZoneBoundary
from .serializers import ZoneSerializer, ZoneBoundarySerializer

class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all().order_by('id')
    serializer_class = ZoneSerializer

class ZoneBoundaryViewSet(viewsets.ModelViewSet):
    queryset = ZoneBoundary.objects.all().order_by('id')
    serializer_class = ZoneBoundarySerializer


