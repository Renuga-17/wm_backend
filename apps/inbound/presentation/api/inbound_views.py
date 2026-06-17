from rest_framework import viewsets
from apps.inbound.infrastructure.persistence.models import InboundShipment
from .serializers import InboundSerializer

class InboundViewSet(viewsets.ModelViewSet):
    queryset = InboundShipment.objects.all()
    serializer_class = InboundSerializer

