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
            
            # Fetch dimensions if any
            dim = product.dimensions.first()
            if dim:
                rep['product']['dimensions'] = f"{dim.length}x{dim.width}x{dim.height}"
            else:
                rep['product']['dimensions'] = ""
                
            # Add attributes for frontend compatibility
            rep['product']['name'] = product.product_name
            rep['product']['category'] = category_name

        # Resolve bin code from StorageAllocation
        from apps.inventory.infrastructure.persistence.movement_models import StorageAllocation
        allocation = StorageAllocation.objects.filter(product=product).first()
        
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

