import logging
from decimal import Decimal
from django.db.models import Sum
from apps.warehouse.models import Rack
from apps.recommendations.models.bin_allocation import BinAllocation

logger = logging.getLogger(__name__)

class RackSelectionService:
    def get_suitable_racks(self, zone, product_weight):
        logger.info("RackSelectionService: Selecting racks for zone %s, product_weight %s", zone.zone_name, product_weight)
        suitable_racks = []
        racks = Rack.objects.filter(zone=zone)
        
        for rack in racks:
            allocated = BinAllocation.objects.filter(rack=rack).aggregate(total_w=Sum('product__weight'))
            current_weight = Decimal(str(allocated['total_w'] or 0.00))
            
            if current_weight + Decimal(str(product_weight)) <= Decimal(str(rack.max_weight)):
                suitable_racks.append(rack)
            else:
                logger.info(
                    "RackSelectionService: Excluding rack %s because capacity is exceeded (current: %s, max: %s, product: %s)",
                    rack.rack_code, current_weight, rack.max_weight, product_weight
                )
                
        return suitable_racks
