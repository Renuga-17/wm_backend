from rest_framework import viewsets
from common.permissions import ReadOnlyOrAuthenticated
from apps.inventory.infrastructure.persistence.models import StockMovement, StorageAllocation
from .serializers import MovementSerializer, StorageAllocationSerializer

class MovementViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = StockMovement.objects.all().order_by('-moved_at', '-id')
    serializer_class = MovementSerializer

class StorageAllocationViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = StorageAllocation.objects.all().order_by('-allocated_at', '-id')
    serializer_class = StorageAllocationSerializer


