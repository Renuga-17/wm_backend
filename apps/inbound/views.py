from rest_framework import viewsets
from .models import Inbound
from .serializers import InboundSerializer

class InboundViewSet(viewsets.ModelViewSet):
    queryset = Inbound.objects.all()
    serializer_class = InboundSerializer
