import logging
from decimal import Decimal
from django.db.models import Sum
from apps.warehouse.models import Rack
from apps.recommendations.models.bin_allocation import BinAllocation
from .dimension_validation import safe_decimal

logger = logging.getLogger(__name__)

class RackSelectionService:
    def get_suitable_racks(self, zone, product_weight):
        warehouse_id = getattr(zone.warehouse, 'id', None)
        p_w = safe_decimal(product_weight, Decimal('0.00'), 'product_weight', f"Zone:{zone.zone_name}", warehouse_id)
        logger.info("RackSelectionService: Selecting racks for zone %s, product_weight %s", zone.zone_name, p_w)
        suitable_racks = []
        racks = Rack.objects.filter(zone=zone)
        
        # Aggregate allocated weights in a single bulk query to prevent N+1 queries
        alloc_weights = BinAllocation.objects.filter(
            rack__in=racks
        ).values('rack_id').annotate(
            total_w=Sum('product__weight')
        )
        weight_map = {w['rack_id']: w['total_w'] for w in alloc_weights}

        for rack in racks:
            allocated_weight = weight_map.get(rack.id)
            current_weight = safe_decimal(allocated_weight, Decimal('0.00'), 'rack_alloc', rack.rack_code, warehouse_id)
            max_weight = safe_decimal(rack.max_weight, Decimal('0.00'), 'max_weight', rack.rack_code, warehouse_id)
            
            if current_weight + p_w <= max_weight:
                suitable_racks.append(rack)
            else:
                logger.info(
                    "RackSelectionService: Excluding rack %s because capacity is exceeded (current: %s, max: %s, product: %s)",
                    rack.rack_code, current_weight, max_weight, p_w
                )
                
        return suitable_racks
