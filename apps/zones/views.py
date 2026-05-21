from rest_framework import viewsets
from .models import Zone
from .serializers import ZoneSerializer

class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
