import logging
from decimal import Decimal
from .dimension_validation import ValidatedDimension

logger = logging.getLogger(__name__)

class DimensionCompatibilityService:
    def check_compatibility(
        self,
        product_dim: ValidatedDimension = None,
        bin_dim: ValidatedDimension = None,
        product_len = None,
        product_width = None,
        product_height = None,
        bin_len = None,
        bin_width = None,
        bin_height = None,
        allow_vertical_stack = True
    ):
        """
        Evaluates all 6 possible product rotations and computes the orientation that yields the maximum number of units that can fit in the bin.
        For fragile or non‑stackable products, vertical stacking is disabled (height layer capped to 1).

        Returns a dictionary with:
            fits: bool – whether any orientation fits
            orientation: tuple – the dimensions of the chosen rotation
            orientation_str: str – human‑readable string e.g., "40x30x20"
            max_units: int – maximum number of product units that can be placed with this orientation
            utilization_score: float – (product_volume * max_units) / bin_volume
        """
        if product_dim is not None:
            p_l = product_dim.length
            p_w = product_dim.width
            p_h = product_dim.height
        else:
            p_l = Decimal(str(product_len)) if product_len is not None else Decimal('0.00')
            p_w = Decimal(str(product_width)) if product_width is not None else Decimal('0.00')
            p_h = Decimal(str(product_height)) if product_height is not None else Decimal('0.00')
        
        if bin_dim is not None:
            b_l = bin_dim.length
            b_w = bin_dim.width
            b_h = bin_dim.height
        else:
            b_l = Decimal(str(bin_len)) if bin_len is not None else Decimal('100.00')
            b_w = Decimal(str(bin_width)) if bin_width is not None else Decimal('100.00')
            b_h = Decimal(str(bin_height)) if bin_height is not None else Decimal('100.00')
        
        # The 6 rotations
        rotations = [
            (p_l, p_w, p_h),
            (p_l, p_h, p_w),
            (p_w, p_l, p_h),
            (p_w, p_h, p_l),
            (p_h, p_l, p_w),
            (p_h, p_w, p_l),
        ]
        
        best = None
        best_score = -1
        for rot in rotations:
            o_l, o_w, o_h = rot
            if o_l <= b_l and o_w <= b_w and o_h <= b_h:
                # compute how many units fit
                units_l = int(b_l // o_l)
                units_w = int(b_w // o_w)
                if allow_vertical_stack:
                    units_h = int(b_h // o_h)
                else:
                    # vertical stacking disabled – only one layer if height fits
                    units_h = 1 if o_h <= b_h else 0
                max_units = units_l * units_w * units_h
                # utilization score based on used volume
                product_volume = float(o_l * o_w * o_h)
                bin_volume = float(b_l * b_w * b_h)
                utilization_score = (product_volume * max_units) / bin_volume if bin_volume > 0 else 0.0
                if max_units > 0 and utilization_score > best_score:
                    best = {
                        'orientation': rot,
                        'orientation_str': "x".join([
                            str(int(val)) if float(val).is_integer() else str(float(val))
                            for val in rot
                        ]),
                        'max_units': max_units,
                        'utilization_score': utilization_score,
                    }
                    best_score = utilization_score
        if best:
            logger.info(
                "DimensionCompatibilityService: Best orientation %s with %d units (utilization %.4f) in bin (%s, %s, %s)",
                best['orientation_str'], best['max_units'], best['utilization_score'], b_l, b_w, b_h,
            )
            return {
                'fits': True,
                'orientation': best['orientation'],
                'orientation_str': best['orientation_str'],
                'max_units': best['max_units'],
                'utilization_score': best['utilization_score'],
            }
        logger.info(
            "DimensionCompatibilityService: No orientation of (%s, %s, %s) fits in bin (%s, %s, %s)",
            p_l, p_w, p_h, b_l, b_w, b_h,
        )
        return {
            'fits': False,
            'orientation': None,
            'orientation_str': None,
            'max_units': 0,
            'utilization_score': 0.0,
        }
