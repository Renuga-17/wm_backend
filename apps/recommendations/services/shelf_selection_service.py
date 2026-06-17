import logging
from decimal import Decimal
from django.db.models import Sum
from apps.warehouse.models import Shelf
from apps.recommendations.models.bin_allocation import BinAllocation

logger = logging.getLogger(__name__)

class ShelfSelectionService:
    def get_suitable_shelves(self, racks, product_weight):
        logger.info("ShelfSelectionService: Selecting shelves for racks and product_weight %s", product_weight)
        suitable_shelves = []
        shelves = Shelf.objects.filter(rack__in=racks)
        
        for shelf in shelves:
            allocated = BinAllocation.objects.filter(shelf=shelf).aggregate(total_w=Sum('product__weight'))
            current_weight = Decimal(str(allocated['total_w'] or 0.00))
            
            if current_weight + Decimal(str(product_weight)) <= Decimal(str(shelf.max_weight)):
                suitable_shelves.append(shelf)
            else:
                logger.info(
                    "ShelfSelectionService: Excluding shelf %s on rack %s (current: %s, max: %s, product: %s)",
                    shelf.shelf_number, shelf.rack.rack_code, current_weight, shelf.max_weight, product_weight
                )
                
        return suitable_shelves
