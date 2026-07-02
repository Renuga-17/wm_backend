import logging
from decimal import Decimal
from django.db.models import Sum
from apps.warehouse.models import Shelf
from apps.recommendations.models.bin_allocation import BinAllocation
from .dimension_validation import safe_decimal

logger = logging.getLogger(__name__)

class ShelfSelectionService:
    def get_suitable_shelves(self, racks, product_weight):
        warehouse_id = None
        if racks:
            try:
                # racks is a QuerySet or a list
                first_rack = racks[0] if hasattr(racks, '__getitem__') else racks.first()
                if first_rack and hasattr(first_rack, 'zone') and first_rack.zone:
                    warehouse_id = getattr(first_rack.zone, 'warehouse_id', None)
            except Exception:
                pass

        p_w = safe_decimal(product_weight, Decimal('0.00'), 'product_weight', 'racks_list', warehouse_id)
        logger.info("ShelfSelectionService: Selecting shelves for racks and product_weight %s", p_w)
        suitable_shelves = []
        # Pre-fetch rack to avoid N+1 query when logging shelf.rack.rack_code
        shelves = Shelf.objects.filter(rack__in=racks).select_related('rack')
        
        # Aggregate allocated weights in a single bulk query to prevent N+1 queries
        alloc_weights = BinAllocation.objects.filter(
            shelf__in=shelves
        ).values('shelf_id').annotate(
            total_w=Sum('product__weight')
        )
        weight_map = {w['shelf_id']: w['total_w'] for w in alloc_weights}

        for shelf in shelves:
            allocated_weight = weight_map.get(shelf.id) or Decimal('0.00')
            current_weight = safe_decimal(allocated_weight, Decimal('0.00'), 'shelf_alloc', shelf.id, warehouse_id)
            max_weight = safe_decimal(shelf.max_weight, Decimal('0.00'), 'max_weight', shelf.id, warehouse_id)
            
            if current_weight + p_w <= max_weight:
                suitable_shelves.append(shelf)
            else:
                logger.info(
                    "ShelfSelectionService: Excluding shelf %s on rack %s (current: %s, max: %s, product: %s)",
                    shelf.shelf_number, shelf.rack.rack_code, current_weight, max_weight, p_w
                )
                
        return suitable_shelves
