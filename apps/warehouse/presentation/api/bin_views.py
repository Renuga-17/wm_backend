from rest_framework import viewsets
from apps.warehouse.infrastructure.persistence.models import Bin
from .serializers import BinSerializer
from common.permissions import ReadOnlyOrAuthenticated


class BinViewSet(viewsets.ModelViewSet):
    queryset = Bin.objects.all()
    serializer_class = BinSerializer
    permission_classes = [ReadOnlyOrAuthenticated]
