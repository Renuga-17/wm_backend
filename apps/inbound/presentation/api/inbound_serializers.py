from rest_framework import serializers
from apps.inbound.infrastructure.persistence.inbound_models import InboundShipmentLine, InboundShipment

class InboundShipmentLineSerializer(serializers.ModelSerializer):
    productName = serializers.CharField(source='product_name', read_only=True)
    verifiedQuantity = serializers.IntegerField(source='quantity', read_only=True)
    quantityReceived = serializers.IntegerField(source='quantity', read_only=True)
    binRecommendationStatus = serializers.CharField(source='recommendation_status', read_only=True)

    class Meta:
        model = InboundShipmentLine
        fields = [
            'id', 'sku', 'product_name', 'productName', 'quantity',
            'verifiedQuantity', 'quantityReceived', 'weight', 'dimensions',
            'storage_type', 'recommendation_status', 'binRecommendationStatus'
        ]


class InboundSerializer(serializers.ModelSerializer):
    line_items = InboundShipmentLineSerializer(many=True, read_only=True)
    supplier = serializers.CharField(source='supplier_name', read_only=True)
    document_reference = serializers.SerializerMethodField()

    class Meta:
        model = InboundShipment
        fields = [
            'id', 'shipment_code', 'supplier_name', 'supplier',
            'expected_arrival', 'status', 'ocr_document', 'document_reference',
            'line_items'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        lines_data = None
        if request and request.data:
            lines_data = request.data.get('line_items') or request.data.get('items')
            
        shipment = InboundShipment.objects.create(**validated_data)
        
        if lines_data:
            for line in lines_data:
                sku = line.get('sku')
                qty = line.get('quantity') or line.get('qty') or 50
                weight_val = line.get('weight') or 0.0
                dim_str = line.get('dimensions') or '10x8x6 cm'
                storage_type = line.get('storage_type') or 'GENERAL'
                prod_name = line.get('product_name') or line.get('productName') or sku
                
                product_obj = None
                if sku:
                    from apps.inventory.infrastructure.persistence.models import Product, ProductCategory
                    category, _ = ProductCategory.objects.get_or_create(category_name='General')
                    product_obj, _ = Product.objects.get_or_create(
                        sku=sku,
                        defaults={
                            'product_name': prod_name,
                            'category': category,
                            'weight': weight_val
                        }
                    )
                
                InboundShipmentLine.objects.create(
                    shipment=shipment,
                    product=product_obj,
                    sku=sku,
                    product_name=prod_name,
                    quantity=qty,
                    weight=weight_val,
                    dimensions=dim_str,
                    storage_type=storage_type
                )
        return shipment

    def get_document_reference(self, instance):
        if instance.ocr_document:
            return instance.ocr_document.file_name
        return "REF-GEN"

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        
        # Flattened compatibility for first product in the shipment (for single item UI)
        lines = list(instance.line_items.all())
        first_line = lines[0] if lines else None
        if first_line:
            rep['sku'] = first_line.sku
            rep['product_name'] = first_line.product_name
            rep['productName'] = first_line.product_name
            rep['product'] = first_line.product_name
            rep['productId'] = str(first_line.product.id) if first_line.product else None
            rep['quantity'] = first_line.quantity
            rep['verifiedQuantity'] = first_line.quantity
            rep['quantityReceived'] = first_line.quantity
            rep['weight'] = f"{first_line.weight} kg"
            rep['dimensions'] = first_line.dimensions
            
            # Map recommendation/allocation status
            mapped_status = 'WAITING_FOR_BIN_ASSIGNMENT'
            if first_line.recommendation_status == 'RECOMMENDED':
                # Check if there is an active BinAllocation confirmed/allocated
                from apps.recommendations.models.bin_allocation import BinAllocation
                allocs = list(first_line.bin_allocations.all())
                alloc = allocs[0] if allocs else None
                if alloc:
                    if alloc.storage_status == BinAllocation.StorageStatus.STORED:
                        mapped_status = 'STORED'
                    elif alloc.storage_status == BinAllocation.StorageStatus.IN_PROGRESS:
                        mapped_status = 'BIN_SUGGESTED'
                    else:
                        mapped_status = 'BIN_SUGGESTED'
                else:
                    mapped_status = 'WAITING_FOR_BIN_ASSIGNMENT'
            elif first_line.recommendation_status == 'STORED':
                mapped_status = 'STORED'
            
            rep['binRecommendationStatus'] = mapped_status
            
            # Also override top-level status for frontend context to match expected
            if instance.status == 'RECEIVED' or instance.status == 'COMPLETED':
                rep['status'] = mapped_status
            else:
                rep['status'] = instance.status
        else:
            rep['sku'] = None
            rep['product_name'] = None
            rep['productName'] = None
            rep['product'] = None
            rep['quantity'] = 0
            rep['verifiedQuantity'] = 0
            rep['quantityReceived'] = 0
            rep['weight'] = None
            rep['dimensions'] = None
            rep['binRecommendationStatus'] = instance.status
            
        # Ensure camelCase support
        rep['shipmentCode'] = instance.shipment_code
        rep['expectedArrival'] = instance.expected_arrival.isoformat() if instance.expected_arrival else None
        rep['supplierName'] = instance.supplier_name
        
        return rep
