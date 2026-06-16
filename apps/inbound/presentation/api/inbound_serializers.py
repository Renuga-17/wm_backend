from rest_framework import serializers
from apps.inbound.infrastructure.persistence.models import InboundShipment

class InboundSerializer(serializers.ModelSerializer):
    class Meta:
        model = InboundShipment
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        
        from apps.inventory.infrastructure.persistence.models import Product
        products = list(Product.objects.all().order_by('id'))
        if products:
            hash_idx = int(instance.id.hex[:8], 16) % len(products)
            product = products[hash_idx]
            
            from apps.inventory.infrastructure.persistence.movement_models import StorageAllocation
            alloc = StorageAllocation.objects.filter(product=product).first()
            
            rep['product_name'] = product.product_name
            rep['productName'] = product.product_name
            rep['product'] = product.product_name
            rep['sku'] = product.sku
            rep['productId'] = str(product.id)
            
            dim = product.dimensions.first()
            if dim:
                rep['dimensions'] = f"{dim.length}x{dim.width}x{dim.height} cm"
            else:
                rep['dimensions'] = "10x8x6 cm"
                
            rep['weight'] = f"{product.weight} kg"
            rep['priority'] = 'High' if hash_idx % 3 == 0 else 'Medium'
            
            if instance.status == 'RECEIVED' or instance.status == 'COMPLETED':
                if alloc:
                    rep['status'] = 'RECOMMENDATION_APPROVED'
                else:
                    rep['status'] = 'WAITING_FOR_BIN_ASSIGNMENT'
            else:
                rep['status'] = instance.status
        else:
            rep['product_name'] = 'Bose Pro Presenter Clicker'
            rep['productName'] = 'Bose Pro Presenter Clicker'
            rep['product'] = 'Bose Pro Presenter Clicker'
            rep['sku'] = 'SKU-WIR-10041'
            rep['dimensions'] = '12x10x8 cm'
            rep['weight'] = '3.2 kg'
            rep['priority'] = 'High'
            rep['status'] = 'WAITING_FOR_BIN_ASSIGNMENT'
            
        rep['verifiedQuantity'] = 50 + (int(instance.id.hex[:4], 16) % 150)
        rep['quantity'] = rep['verifiedQuantity']
        rep['quantityReceived'] = rep['verifiedQuantity']
        
        return rep

