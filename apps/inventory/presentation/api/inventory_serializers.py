from rest_framework import serializers
from apps.inventory.infrastructure.persistence.models import Inventory, Product, ProductCategory
from .product_serializers import ProductSerializer

class InventorySerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Inventory
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        product = instance.product
        
        category_name = ""
        if product and product.category:
            category_name = product.category.category_name
            
        if product:
            rep['sku'] = product.sku
            rep['product_name'] = product.product_name
            rep['category'] = category_name
            
            # Fetch dimensions if any (use prefetched list to avoid N+1 query)
            dims = list(product.dimensions.all())
            dim = dims[0] if dims else None
            if dim:
                rep['product']['dimensions'] = f"{dim.length}x{dim.width}x{dim.height}"
            else:
                rep['product']['dimensions'] = ""
                
            # Add attributes for frontend compatibility
            rep['product']['name'] = product.product_name
            rep['product']['category'] = category_name

        # Resolve bin code from StorageAllocation (use prefetched list to avoid N+1 query)
        allocations = list(product.allocations.all()) if product else []
        allocation = allocations[0] if allocations else None
        
        bin_code = ""
        shelf_num = ""
        rack_code = ""
        zone_name = ""
        warehouse_name = ""
        
        if allocation and allocation.bin:
            bin_code = allocation.bin.bin_code
            if allocation.bin.shelf:
                shelf_num = str(allocation.bin.shelf.shelf_number)
                if allocation.bin.shelf.rack:
                    rack_code = allocation.bin.shelf.rack.rack_code
                    if allocation.bin.shelf.rack.zone:
                        zone_name = allocation.bin.shelf.rack.zone.zone_name
                        if allocation.bin.shelf.rack.zone.warehouse:
                            warehouse_name = allocation.bin.shelf.rack.zone.warehouse.name
        
        rep['bin'] = bin_code
        rep['bin_code'] = bin_code
        rep['shelf'] = shelf_num
        rep['rack_name'] = rack_code
        rep['zone'] = zone_name
        rep['zone_name'] = zone_name
        rep['warehouse'] = warehouse_name
        rep['warehouse_name'] = warehouse_name
        
        return rep


class ProductRelocationSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=100)
    from_bin_id = serializers.CharField(max_length=100)
    to_bin_id = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1)
    operator = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')


class BinTransferSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=100)
    from_bin_id = serializers.CharField(max_length=100)
    to_bin_id = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1)
    operator = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')


class StockAdjustmentSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=100)
    bin_id = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField()
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default='Manual adjustment')
    operator = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')


class DamageReportSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=100)
    bin_id = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default='Damaged')
    operator = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')


class InventoryAuditSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=100)
    bin_id = serializers.CharField(max_length=100)
    physical_count = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default='Stocktake audit')
    operator = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')


