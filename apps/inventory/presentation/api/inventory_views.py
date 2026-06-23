from rest_framework import viewsets
from django.db.models import Prefetch
from apps.inventory.infrastructure.persistence.models import Inventory, StorageAllocation
from .serializers import InventorySerializer

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all().select_related(
        'product',
        'product__category'
    ).prefetch_related(
        'product__dimensions',
        Prefetch(
            'product__allocations',
            queryset=StorageAllocation.objects.all().select_related(
                'bin',
                'bin__shelf',
                'bin__shelf__rack',
                'bin__shelf__rack__zone',
                'bin__shelf__rack__zone__warehouse'
            )
        )
    )
    serializer_class = InventorySerializer
