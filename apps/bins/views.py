from rest_framework import viewsets
from .models import Bin
from .serializers import BinSerializer

class BinViewSet(viewsets.ModelViewSet):
    queryset = Bin.objects.all()
    serializer_class = BinSerializer
