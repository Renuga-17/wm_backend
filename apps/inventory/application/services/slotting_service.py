import decimal
from django.db.models import F
from apps.inventory.infrastructure.persistence.models import Product, ProductStorageRule
from apps.warehouse.infrastructure.persistence.models import Zone, WarehouseHeatmap
from apps.warehouse.infrastructure.persistence.models import Rack
from apps.warehouse.infrastructure.persistence.models import Shelf, Bin


class SlottingEngineError(Exception):
    pass


class SlottingService:
    
    @classmethod
    def recommend_storage_location(cls, product_id, quantity):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise SlottingEngineError("Product not found.")
            
        quantity = decimal.Decimal(str(quantity))
        total_weight = product.weight * quantity
            
        zone = cls.find_best_zone(product)
        if not zone:
            raise SlottingEngineError("No suitable zone found for product storage rules.")
            
        rack = cls.find_best_rack(zone, total_weight)
        if not rack:
            raise SlottingEngineError("No suitable rack found with sufficient weight capacity.")
            
        shelf = cls.find_best_shelf(rack, total_weight)
        if not shelf:
            raise SlottingEngineError("No suitable shelf found with sufficient weight capacity.")
            
        bin_obj = cls.find_best_bin(shelf, quantity)
        if not bin_obj:
            raise SlottingEngineError("No suitable bin found with sufficient capacity.")
            
        return {
            "zone": str(zone.id),
            "rack": str(rack.id),
            "shelf": str(shelf.id),
            "bin": str(bin_obj.id),
            "bin_code": bin_obj.bin_code
        }

    @classmethod
    def find_best_zone(cls, product):
        rules = ProductStorageRule.objects.filter(product=product).first()
        zones = Zone.objects.all()
        
        if rules and rules.allowed_zone_type:
            zones = zones.filter(zone_type=rules.allowed_zone_type)
            
        # Select zone with lowest average heatmap score
        best_zone = None
        lowest_score = float('inf')
        
        for zone in zones:
            heatmap = WarehouseHeatmap.objects.filter(zone=zone).order_by('-generated_at').first()
            score = float(heatmap.activity_score) if heatmap else 0.0
            if score < lowest_score:
                lowest_score = score
                best_zone = zone
                
        return best_zone or zones.first()

    @classmethod
    def find_best_rack(cls, zone, total_weight):
        # Find racks in zone that can support the additional weight.
        racks = Rack.objects.filter(zone=zone, max_weight__gte=total_weight)
        return racks.first()

    @classmethod
    def find_best_shelf(cls, rack, total_weight):
        shelves = Shelf.objects.filter(rack=rack, max_weight__gte=total_weight)
        # Prioritize lower shelves for items
        return shelves.order_by('height_from_ground').first()

    @classmethod
    def find_best_bin(cls, shelf, quantity):
        # Bin capacity logic: max_capacity >= current_capacity + quantity
        # First try completely unoccupied bins
        bins = Bin.objects.filter(
            shelf=shelf,
            is_occupied=False,
            max_capacity__gte=F('current_capacity') + quantity
        )
        if not bins.exists():
            # Fallback to occupied bins with enough space
            bins = Bin.objects.filter(
                shelf=shelf,
                max_capacity__gte=F('current_capacity') + quantity
            )
        return bins.first()
