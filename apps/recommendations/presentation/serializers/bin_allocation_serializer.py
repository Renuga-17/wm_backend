from rest_framework import serializers
from ...models.bin_allocation import BinAllocation

class BinAllocationInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=True)

class BinAllocationOutputSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source='product.id')
    zone_group = serializers.CharField(source='zone_group.code')
    zone = serializers.CharField(source='zone.zone_name')
    rack = serializers.SerializerMethodField()
    shelf = serializers.SerializerMethodField()
    bin = serializers.SerializerMethodField()

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
            'allocation_version'
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
