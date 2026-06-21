from rest_framework import serializers
from apps.warehouse.infrastructure.persistence.models import Warehouse, Rack, SpatialEntity, NavigationNode, WarehousePath, RackCoordinate, NavigationEdge

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'

class RackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rack
        fields = '__all__'

class SpatialEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SpatialEntity
        fields = '__all__'

class NavigationNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavigationNode
        fields = '__all__'

class WarehousePathSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehousePath
        fields = '__all__'

class RackCoordinateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RackCoordinate
        fields = '__all__'


class NavigationEdgeSerializer(serializers.ModelSerializer):
    from_node_name = serializers.CharField(source='from_node.node_name', read_only=True)
    to_node_name = serializers.CharField(source='to_node.node_name', read_only=True)

    class Meta:
        model = NavigationEdge
        fields = [
            'id', 'warehouse', 'from_node', 'from_node_name', 
            'to_node', 'to_node_name', 'edge_weight', 
            'congestion_score', 'is_blocked', 'travel_time', 'dynamic_cost'
        ]



