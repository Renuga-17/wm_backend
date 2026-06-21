from rest_framework import viewsets
from apps.inventory.infrastructure.persistence.models import StockMovement, StorageAllocation
from .serializers import MovementSerializer, StorageAllocationSerializer

class MovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = MovementSerializer

class StorageAllocationViewSet(viewsets.ModelViewSet):
    queryset = StorageAllocation.objects.all()
    serializer_class = StorageAllocationSerializer

