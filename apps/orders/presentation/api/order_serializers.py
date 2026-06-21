from rest_framework import serializers
from apps.orders.infrastructure.persistence.models import OutboundShipment

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutboundShipment
        fields = ['id', 'shipment_code', 'customer_name', 'dispatch_time', 'status', 'items', 'picklist']

class GeneratePickListSerializer(serializers.Serializer):
    shipment_id = serializers.CharField(max_length=100)

class AssignPickerSerializer(serializers.Serializer):
    picklist_id = serializers.CharField(max_length=100)
    operator = serializers.CharField(max_length=150)

class OptimizeRouteSerializer(serializers.Serializer):
    picklist_id = serializers.CharField(max_length=100)
    start_node_id = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')

class PackedItemSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=0)

class PackItemsSerializer(serializers.Serializer):
    picklist_id = serializers.CharField(max_length=100)
    packed_items = PackedItemSerializer(many=True)

class OutboundOperationSerializer(serializers.Serializer):
    picklist_id = serializers.CharField(max_length=100)
