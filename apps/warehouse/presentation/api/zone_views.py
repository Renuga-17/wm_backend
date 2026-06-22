from rest_framework import viewsets
from apps.warehouse.infrastructure.persistence.models import Zone, ZoneBoundary, ZoneGroup, Aisle
from .serializers import ZoneSerializer, ZoneBoundarySerializer, ZoneGroupSerializer, AisleSerializer
from common.permissions import ReadOnlyOrAuthenticated


class ZoneGroupViewSet(viewsets.ModelViewSet):
    queryset = ZoneGroup.objects.all().order_by('id')
    serializer_class = ZoneGroupSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class AisleViewSet(viewsets.ModelViewSet):
    queryset = Aisle.objects.all().order_by('id')
    serializer_class = AisleSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all().order_by('id')
    serializer_class = ZoneSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class ZoneBoundaryViewSet(viewsets.ModelViewSet):
    queryset = ZoneBoundary.objects.all().order_by('id')
    serializer_class = ZoneBoundarySerializer
    permission_classes = [ReadOnlyOrAuthenticated]
