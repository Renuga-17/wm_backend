from rest_framework import viewsets
from .models import Rack
from .serializers import RackSerializer

class RackViewSet(viewsets.ModelViewSet):
    queryset = Rack.objects.all()
    serializer_class = RackSerializer
