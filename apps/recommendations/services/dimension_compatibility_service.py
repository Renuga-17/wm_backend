import logging
from decimal import Decimal
from .dimension_validation import ValidatedDimension

logger = logging.getLogger(__name__)

class DimensionCompatibilityService:
    def check_compatibility(self, product_dim: ValidatedDimension, bin_dim: ValidatedDimension):
        """
        Evaluates all 6 possible product rotations:
        - L×W×H
        - L×H×W
        - W×L×H
        - W×H×L
        - H×L×W
        - H×W×L
        
        Returns the first orientation that fits as a dictionary.
        """
        p_l = product_dim.length
        p_w = product_dim.width
        p_h = product_dim.height
        
        b_l = bin_dim.length
        b_w = bin_dim.width
        b_h = bin_dim.height
        
        # The 6 rotations
        rotations = [
            (p_l, p_w, p_h),
            (p_l, p_h, p_w),
            (p_w, p_l, p_h),
            (p_w, p_h, p_l),
            (p_h, p_l, p_w),
            (p_h, p_w, p_l),
        ]
        
        for rot in rotations:
            o_l, o_w, o_h = rot
            if o_l <= b_l and o_w <= b_w and o_h <= b_h:
                # Format rotation string: 40x30x20
                parts = []
                for val in rot:
                    f_val = float(val)
                    if f_val.is_integer():
                        parts.append(str(int(f_val)))
                    else:
                        parts.append(str(f_val))
                orientation_str = "x".join(parts)
                logger.info(
                    "DimensionCompatibilityService: Fitting orientation %s in bin (%s, %s, %s)",
                    orientation_str, b_l, b_w, b_h
                )
                return {
                    'fits': True,
                    'orientation': rot,
                    'orientation_str': orientation_str
                }
                
        logger.info(
            "DimensionCompatibilityService: No orientation of (%s, %s, %s) fits in bin (%s, %s, %s)",
            p_l, p_w, p_h, b_l, b_w, b_h
        )
        return {
            'fits': False,
            'orientation': None,
            'orientation_str': None
        }
