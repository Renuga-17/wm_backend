from rest_framework import viewsets
from .models import OutboundShipment
from .serializers import OrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = OutboundShipment.objects.all()
    serializer_class = OrderSerializer

