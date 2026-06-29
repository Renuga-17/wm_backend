import logging
import math
from decimal import Decimal
from django.db.models import Sum, Max
from apps.warehouse.models import Bin, Shelf
from apps.recommendations.models.bin_allocation import BinAllocation
from .dimension_compatibility_service import DimensionCompatibilityService
from .dimension_validation import (
    validate_bin_dimensions,
    validate_product_dimensions,
    DimensionValidationError,
    safe_decimal
)

logger = logging.getLogger(__name__)

class BinSelectionService:
    def __init__(self):
        self.dimension_service = DimensionCompatibilityService()

    def get_best_bin(self, shelves, product, product_dimension):
        """
        Filters and scores bins within the suitable shelves.
        Returns:
            (best_bin, selected_orientation, best_score, allocation_reason)
            or (None, None, 0.0, reason)
        """
        logger.info(
            "BinSelectionService: Selecting bin from %d shelves for product %s",
            len(shelves), product.sku
        )
        
        bins = Bin.objects.filter(shelf__in=shelves)
        candidate_bins = []

        product_weight = safe_decimal(product.weight, Decimal('0.00'), 'weight', product.sku)
        
        try:
            p_dim = validate_product_dimensions(product_dimension)
        except DimensionValidationError as e:
            logger.error("BinSelectionService: Invalid product dimensions: %s", str(e))
            return None, None, 0.0, f"Invalid product dimensions: {str(e)}"

        for bin_obj in bins:
            # 1. Occupancy check
            if bin_obj.is_occupied:
                logger.info("BinSelectionService: Bin %s is occupied, skipping.", bin_obj.bin_code)
                continue

            # 2. Capacity check
            if bin_obj.current_capacity >= bin_obj.max_capacity:
                logger.info(
                    "BinSelectionService: Bin %s is at max capacity (%s/%s), skipping.",
                    bin_obj.bin_code, bin_obj.current_capacity, bin_obj.max_capacity
                )
                continue

            # 3. Dimension Compatibility Check (evaluating all 6 product rotations)
            try:
                b_dim = validate_bin_dimensions(bin_obj)
            except DimensionValidationError as e:
                logger.warning("BinSelectionService: Skipping bin %s due to dimension validation error: %s", bin_obj.bin_code, str(e))
                continue

            compat = self.dimension_service.check_compatibility(
                product_dim=p_dim,
                bin_dim=b_dim
            )
            if not compat['fits']:
                logger.info(
                    "BinSelectionService: Product dimensions %s did not fit in bin %s (%s, %s, %s), skipping.",
                    f"{p_dim.length}x{p_dim.width}x{p_dim.height}", bin_obj.bin_code, b_dim.length, b_dim.width, b_dim.height
                )
                continue

            # 4. Scoring the bin
            # 4.1 Capacity Score (available % of max)
            max_cap = float(bin_obj.max_capacity)
            curr_cap = float(bin_obj.current_capacity)
            capacity_score = (max_cap - curr_cap) / max_cap if max_cap > 0.0 else 0.0
            capacity_score = max(0.0, min(1.0, capacity_score))

            # 4.2 Utilisation Score (inverse of current utilisation)
            utilisation_score = 1.0 - (curr_cap / max_cap) if max_cap > 0.0 else 0.0
            utilisation_score = max(0.0, min(1.0, utilisation_score))

            # 4.3 Weight Score (rack/shelf headroom)
            rack = bin_obj.shelf.rack
            shelf = bin_obj.shelf
            warehouse_id = getattr(rack.zone.warehouse, 'id', None)

            # Sum existing weights
            rack_alloc = BinAllocation.objects.filter(rack=rack).aggregate(total_w=Sum('product__weight'))['total_w'] or Decimal('0.00')
            rack_curr = safe_decimal(rack_alloc, Decimal('0.00'), 'rack_alloc', rack.rack_code, warehouse_id)
            rack_max = safe_decimal(rack.max_weight, Decimal('0.00'), 'max_weight', rack.rack_code, warehouse_id)
            rack_headroom = float(rack_max - rack_curr - product_weight) / float(rack_max) if rack_max > 0.0 else 0.0
            rack_headroom = max(0.0, min(1.0, rack_headroom))

            shelf_alloc = BinAllocation.objects.filter(shelf=shelf).aggregate(total_w=Sum('product__weight'))['total_w'] or Decimal('0.00')
            shelf_curr = safe_decimal(shelf_alloc, Decimal('0.00'), 'shelf_alloc', shelf.id, warehouse_id)
            shelf_max = safe_decimal(shelf.max_weight, Decimal('0.00'), 'max_weight', shelf.id, warehouse_id)
            shelf_headroom = float(shelf_max - shelf_curr - product_weight) / float(shelf_max) if shelf_max > 0.0 else 0.0
            shelf_headroom = max(0.0, min(1.0, shelf_headroom))

            weight_score = 0.5 * rack_headroom + 0.5 * shelf_headroom

            # 4.4 Proximity Score (distance to aisle centre)
            aisle = rack.aisle
            if aisle and rack.x is not None and rack.y is not None:
                aisle_x = float(aisle.start_x + aisle.end_x) / 2.0
                aisle_y = float(aisle.start_y + aisle.end_y) / 2.0
                dist = math.sqrt((float(rack.x) - aisle_x)**2 + (float(rack.y) - aisle_y)**2)
                proximity_score = 1.0 / (1.0 + dist)
            else:
                proximity_score = 0.5
            proximity_score = max(0.0, min(1.0, proximity_score))

            # 4.5 Shelf Height Score (lower is better)
            all_shelves = Shelf.objects.filter(rack=rack)
            max_height = all_shelves.aggregate(max_h=Max('height_from_ground'))['max_h'] or Decimal('0.00')
            max_height_dec = safe_decimal(max_height, Decimal('0.00'), 'max_height_from_ground', rack.rack_code, warehouse_id)
            max_height_val = float(max_height_dec)
            shelf_height = float(safe_decimal(shelf.height_from_ground, Decimal('0.00'), 'height_from_ground', shelf.id, warehouse_id))
            if max_height_val > 0.0:
                shelf_height_score = 1.0 - (shelf_height / max_height_val)
            else:
                shelf_height_score = 1.0
            shelf_height_score = max(0.0, min(1.0, shelf_height_score))

            # Composite Score
            # Weights: Capacity (35%), Utilisation (25%), Weight (20%), Proximity (15%), Height (5%)
            score = (
                0.35 * capacity_score +
                0.25 * utilisation_score +
                0.20 * weight_score +
                0.15 * proximity_score +
                0.05 * shelf_height_score
            )
            score = max(0.0, min(1.0, score))

            candidate_bins.append({
                'bin': bin_obj,
                'orientation': compat['orientation_str'],
                'score': score,
                'reasons': (
                    f"CapScore: {capacity_score:.2f}, UtilScore: {utilisation_score:.2f}, "
                    f"WeightScore: {weight_score:.2f}, ProxScore: {proximity_score:.2f}, "
                    f"HeightScore: {shelf_height_score:.2f}"
                )
            })

        if not candidate_bins:
            logger.info("BinSelectionService: No candidate bins found.")
            return None, None, 0.0, "No candidate bins met dimension and capacity constraints."

        # Sort by score descending
        candidate_bins.sort(key=lambda x: x['score'], reverse=True)
        best_candidate = candidate_bins[0]
        logger.info(
            "BinSelectionService: Selected best bin %s with score %.4f",
            best_candidate['bin'].bin_code, best_candidate['score']
        )
        return (
            best_candidate['bin'],
            best_candidate['orientation'],
            best_candidate['score'],
            f"Optimized bin selected: {best_candidate['reasons']}"
        )
