from rest_framework import serializers
from ...models.bin_allocation import BinAllocation
from .bin_3d_placement_serializer import Bin3DPlacementSerializer
from apps.warehouse.application.services.route_optimizer import RouteOptimizer
from apps.warehouse.infrastructure.persistence.models import NavigationNode

class BinAllocationInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=True)

class BinAllocationOutputSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source='product.id')
    zone_group = serializers.CharField(source='zone_group.code')
    zone = serializers.CharField(source='zone.zone_name')
    rack = serializers.SerializerMethodField()
    shelf = serializers.SerializerMethodField()
    bin = serializers.SerializerMethodField()
    placement_3d = Bin3DPlacementSerializer(read_only=True)
    route = serializers.SerializerMethodField()

    class Meta:
        model = BinAllocation
        fields = [
            'product_id',
            'zone_group',
            'zone',
            'rack',
            'shelf',
            'bin',
            'selected_orientation',
            'allocation_score',
            'allocation_reason',
            'allocation_source',
            'allocation_version',
            'placement_3d',
            'route',
            'navigation_instructions',
            'placement_instructions',
            'storage_status',
            'stored_at',
            'operator'
        ]

    def get_rack(self, obj):
        return {
            "id": str(obj.rack.id),
            "code": obj.rack.rack_code
        }

    def get_shelf(self, obj):
        return {
            "id": str(obj.shelf.id),
            "number": obj.shelf.shelf_number
        }

    def get_bin(self, obj):
        return {
            "id": str(obj.bin.id),
            "code": obj.bin.bin_code
        }

    def get_route(self, obj):
        start_location = "DOCK_A"
        docks = NavigationNode.objects.filter(warehouse=obj.zone.warehouse, node_type__iexact='DOCK')
        dock = docks.first()
        if dock is not None:
            start_location = dock.node_name
        try:
            route_data = RouteOptimizer.compute_route(
                warehouse_id=obj.zone.warehouse.id,
                start_location=start_location,
                target_location=obj.bin.bin_code
            )
            return {
                "distance": route_data.get("distance", 0.0),
                "path": [[float(p["x"]), float(p["y"])] for p in route_data.get("path", [])]
            }
        except Exception:
            return {
                "distance": 0.0,
                "path": []
            }

