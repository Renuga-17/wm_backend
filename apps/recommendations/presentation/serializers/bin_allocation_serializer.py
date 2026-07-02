from rest_framework import serializers
from ...models.bin_allocation import BinAllocation
from .bin_3d_placement_serializer import Bin3DPlacementSerializer
from apps.warehouse.application.services.route_optimizer import RouteOptimizer
from apps.warehouse.infrastructure.persistence.models import NavigationNode

class BinAllocationInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=True)
    inbound_line_id = serializers.UUIDField(required=False, allow_null=True)
    inbound_id = serializers.UUIDField(required=False, allow_null=True)

class BinAllocationOutputSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source='product.id')
    zone_group = serializers.CharField(source='zone_group.code')
    zone = serializers.CharField(source='zone.zone_name')
    rack = serializers.SerializerMethodField()
    shelf = serializers.SerializerMethodField()
    bin = serializers.SerializerMethodField()
    placement_3d = Bin3DPlacementSerializer(read_only=True)
    route = serializers.SerializerMethodField()

    orientation = serializers.SerializerMethodField()
    max_units_fit = serializers.SerializerMethodField()
    utilization_score = serializers.SerializerMethodField()
    placement_instruction = serializers.SerializerMethodField()

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
            'orientation',
            'max_units_fit',
            'utilization_score',
            'placement_instruction',
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

    def get_orientation(self, obj):
        if obj.selected_orientation:
            return obj.selected_orientation
        return "N/A"

    def get_max_units_fit(self, obj):
        if hasattr(obj, 'max_units') and obj.max_units is not None:
            return obj.max_units
        try:
            from apps.inventory.infrastructure.persistence.models import ProductDimension
            product_dim = ProductDimension.objects.filter(product=obj.product).first()
            if product_dim and obj.bin:
                p_l, p_w, p_h = float(product_dim.length), float(product_dim.width), float(product_dim.height)
                b_l, b_w, b_h = float(obj.bin.length), float(obj.bin.width), float(obj.bin.height)
                if p_l > 0 and p_w > 0 and p_h > 0 and b_l > 0 and b_w > 0 and b_h > 0:
                    return int((b_l // p_l) * (b_w // p_w) * (b_h // p_h))
        except Exception:
            pass
        return 1

    def get_utilization_score(self, obj):
        if hasattr(obj, 'utilization_score') and obj.utilization_score is not None:
            return obj.utilization_score
        return 0.0

    def get_placement_instruction(self, obj):
        if hasattr(obj, 'placement_instructions') and obj.placement_instructions:
            return obj.placement_instructions
        try:
            if hasattr(obj, 'placement_3d') and obj.placement_3d:
                strategy = obj.placement_3d.placement_strategy
                return f"Place product in bin {obj.bin.bin_code} using {strategy} strategy."
        except Exception:
            pass
        return f"Place product in bin {obj.bin.bin_code}."

