from rest_framework import serializers
from apps.warehouse.infrastructure.persistence.models import Warehouse, WarehouseLayout

class WarehouseLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseLayout
        fields = '__all__'

class LayoutUploadSerializer(serializers.Serializer):
    warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(), source='warehouse'
    )
    layout_name = serializers.CharField(max_length=100)
    file = serializers.FileField()
    width = serializers.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    height = serializers.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    depth = serializers.DecimalField(max_digits=10, decimal_places=2, default=50.00)

class LayoutAnalysisSerializer(serializers.Serializer):
    layout_id = serializers.UUIDField()

class GenerateTopologySerializer(serializers.Serializer):
    layout_id = serializers.UUIDField()
    shelves_per_rack = serializers.IntegerField(default=4, min_value=1)
    bins_per_shelf = serializers.IntegerField(default=5, min_value=1)
