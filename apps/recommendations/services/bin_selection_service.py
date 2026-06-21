import logging
import math
from decimal import Decimal
from django.db.models import Sum, Max
from apps.warehouse.models import Bin, Shelf
from apps.recommendations.models.bin_allocation import BinAllocation
from .dimension_compatibility_service import DimensionCompatibilityService

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

        product_weight = Decimal(str(product.weight))
        p_l = Decimal(str(product_dimension.length))
        p_w = Decimal(str(product_dimension.width))
        p_h = Decimal(str(product_dimension.height))

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
            compat = self.dimension_service.check_compatibility(
                product_len=p_l,
                product_width=p_w,
                product_height=p_h,
                bin_len=bin_obj.length,
                bin_width=bin_obj.width,
                bin_height=bin_obj.height
            )
            if not compat['fits']:
                logger.info(
                    "BinSelectionService: Product dimensions %s did not fit in bin %s (%s, %s, %s), skipping.",
                    f"{p_l}x{p_w}x{p_h}", bin_obj.bin_code, bin_obj.length, bin_obj.width, bin_obj.height
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

            # Sum existing weights
            rack_alloc = BinAllocation.objects.filter(rack=rack).aggregate(total_w=Sum('product__weight'))['total_w'] or Decimal('0.00')
            rack_curr = Decimal(str(rack_alloc))
            rack_max = Decimal(str(rack.max_weight))
            rack_headroom = float(rack_max - rack_curr - product_weight) / float(rack_max) if rack_max > 0.0 else 0.0
            rack_headroom = max(0.0, min(1.0, rack_headroom))

            shelf_alloc = BinAllocation.objects.filter(shelf=shelf).aggregate(total_w=Sum('product__weight'))['total_w'] or Decimal('0.00')
            shelf_curr = Decimal(str(shelf_alloc))
            shelf_max = Decimal(str(shelf.max_weight))
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
            max_height = float(max_height)
            shelf_height = float(shelf.height_from_ground)
            if max_height > 0.0:
                shelf_height_score = 1.0 - (shelf_height / max_height)
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
