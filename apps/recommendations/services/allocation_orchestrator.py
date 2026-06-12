import logging
from .rack_selection_service import RackSelectionService
from .shelf_selection_service import ShelfSelectionService
from .bin_selection_service import BinSelectionService

logger = logging.getLogger(__name__)

class AllocationOrchestrator:
    def __init__(self):
        self.rack_selector = RackSelectionService()
        self.shelf_selector = ShelfSelectionService()
        self.bin_selector = BinSelectionService()

    def find_allocation(self, zone, product, product_dimension):
        logger.info(
            "AllocationOrchestrator: Running allocation orchestration for product %s in zone %s",
            product.sku, zone.zone_name
        )
        
        # 1. Select suitable racks
        racks = self.rack_selector.get_suitable_racks(zone, product.weight)
        if not racks:
            msg = f"Weight capacity exceeded: No suitable racks available in zone {zone.zone_name} for weight {product.weight}."
            logger.info("AllocationOrchestrator: %s", msg)
            return None, None, 0.0, msg
            
        # 2. Select suitable shelves
        shelves = self.shelf_selector.get_suitable_shelves(racks, product.weight)
        if not shelves:
            msg = f"Weight capacity exceeded: No suitable shelves available on selected racks for weight {product.weight}."
            logger.info("AllocationOrchestrator: %s", msg)
            return None, None, 0.0, msg
            
        # 3. Select and score candidate bins
        bin_obj, orientation, score, reason = self.bin_selector.get_best_bin(shelves, product, product_dimension)
        return bin_obj, orientation, score, reason
