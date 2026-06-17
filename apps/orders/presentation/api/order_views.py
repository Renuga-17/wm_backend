from rest_framework import viewsets
from apps.orders.infrastructure.persistence.models import OutboundShipment
from .serializers import OrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = OutboundShipment.objects.all()
    serializer_class = OrderSerializer

