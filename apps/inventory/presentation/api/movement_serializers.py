from rest_framework import serializers
from apps.inventory.infrastructure.persistence.models import StockMovement, StorageAllocation

class MovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = '__all__'

class StorageAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageAllocation
        fields = '__all__'

