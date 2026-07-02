import logging
from decimal import Decimal
from apps.warehouse.models import Bin
from apps.inventory.infrastructure.persistence.models import Product, ProductDimension
from ..models.bin_allocation import BinAllocation
from ..models.bin_3d_placement import Bin3DPlacement
from .dimension_validation import (
    validate_bin_dimensions,
    validate_product_dimensions,
    DimensionValidationError,
    safe_decimal
)

logger = logging.getLogger(__name__)

class ThreeDOptimizationService:
    def evaluate_placement(self, bin_allocation: BinAllocation) -> Bin3DPlacement:
        """
        Main method to evaluate and persist 3D placement for a completed BinAllocation.
        """
        logger.info("ThreeDOptimizationService: Evaluating 3D placement for allocation %s", bin_allocation.id)
        
        product = bin_allocation.product
        bin_obj = bin_allocation.bin
        warehouse_id = None
        try:
            if bin_obj.shelf and bin_obj.shelf.rack and bin_obj.shelf.rack.zone:
                warehouse_id = getattr(bin_obj.shelf.rack.zone.warehouse, 'id', None)
        except Exception:
            pass

        # 1. Get ProductDimension
        product_dim = ProductDimension.objects.filter(product=product).first()
        if not product_dim:
            logger.error("ThreeDOptimizationService: ProductDimension not found for product %s", product.sku)
            raise ValueError("Product dimensions not found")

        # Validate early
        p_dim = validate_product_dimensions(product_dim)
        b_dim = validate_bin_dimensions(bin_obj)

        # 2. Get existing placements in the same bin (excluding the current one)
        existing_placements = Bin3DPlacement.objects.filter(
            bin_allocation__bin=bin_obj
        ).exclude(bin_allocation=bin_allocation).select_related(
            'bin_allocation',
            'bin_allocation__product'
        ).prefetch_related(
            'bin_allocation__product__dimensions'
        )

        # 3. Calculate volumes
        bin_vol = b_dim.length * b_dim.width * b_dim.height
        product_vol = p_dim.length * p_dim.width * p_dim.height
        
        occupied_vol = Decimal('0.00')
        for placement in existing_placements:
            alloc = placement.bin_allocation
            try:
                l, w, h = map(float, alloc.selected_orientation.split('x'))
                occupied_vol += Decimal(str(l)) * Decimal(str(w)) * Decimal(str(h))
            except Exception:
                # Fallback if selected_orientation parsing fails
                dims = list(alloc.product.dimensions.all())
                dim = dims[0] if dims else None
                if dim:
                    try:
                        validated_dim = validate_product_dimensions(dim)
                        occupied_vol += validated_dim.length * validated_dim.width * validated_dim.height
                    except Exception:
                        dl = safe_decimal(dim.length, Decimal('0.00'), 'length', alloc.product.sku, warehouse_id)
                        dw = safe_decimal(dim.width, Decimal('0.00'), 'width', alloc.product.sku, warehouse_id)
                        dh = safe_decimal(dim.height, Decimal('0.00'), 'height', alloc.product.sku, warehouse_id)
                        occupied_vol += dl * dw * dh

        # Check total remaining volume
        remaining_vol = bin_vol - occupied_vol
        
        # 4. Evaluate orientations
        p_l = p_dim.length
        p_w = p_dim.width
        p_h = p_dim.height

        b_l = b_dim.length
        b_w = b_dim.width
        b_h = b_dim.height

        rotations = [
            (p_l, p_w, p_h, Bin3DPlacement.LabelDirection.FRONT), # L x W x H
            (p_l, p_h, p_w, Bin3DPlacement.LabelDirection.TOP),   # L x H x W
            (p_w, p_l, p_h, Bin3DPlacement.LabelDirection.FRONT), # W x L x H
            (p_w, p_h, p_l, Bin3DPlacement.LabelDirection.SIDE),  # W x H x L
            (p_h, p_l, p_w, Bin3DPlacement.LabelDirection.SIDE),  # H x L x W
            (p_h, p_w, p_l, Bin3DPlacement.LabelDirection.SIDE),  # H x W x L
        ]

        # Calculate exact coordinates (x, y, z) and strategy
        position_x = Decimal('0.00')
        position_y = Decimal('0.00')
        position_z = Decimal('0.00')
        strategy = Bin3DPlacement.PlacementStrategy.BOTTOM_FLAT
        selected_orientation = None
        label_dir = Bin3DPlacement.LabelDirection.FRONT

        if not existing_placements.exists():
            # Bin is empty
            # Find first orientation that fits the bin
            for rot_l, rot_w, rot_h, lbl in rotations:
                if rot_l <= b_l and rot_w <= b_w and rot_h <= b_h:
                    selected_orientation = (rot_l, rot_w, rot_h)
                    label_dir = lbl
                    break
            
            if not selected_orientation:
                raise ValueError("Product does not fit in bin in any orientation")
            
            position_x = Decimal('0.00')
            position_y = Decimal('0.00')
            position_z = Decimal('0.00')
            strategy = Bin3DPlacement.PlacementStrategy.BOTTOM_FLAT
        else:
            # Multi-product packing coordinate heuristic
            # We determine candidates for (x, y, z) by shifting based on existing bounding boxes.
            max_x = Decimal('0.00')
            max_y = Decimal('0.00')
            max_z = Decimal('0.00')

            for p in existing_placements:
                try:
                    l_prev, w_prev, h_prev = map(float, p.bin_allocation.selected_orientation.split('x'))
                except Exception:
                    l_prev, w_prev, h_prev = float(p_dim.length), float(p_dim.width), float(p_dim.height)
                
                pos_x = safe_decimal(p.position_x, Decimal('0.00'), 'position_x', p.id, warehouse_id)
                pos_y = safe_decimal(p.position_y, Decimal('0.00'), 'position_y', p.id, warehouse_id)
                pos_z = safe_decimal(p.position_z, Decimal('0.00'), 'position_z', p.id, warehouse_id)

                max_x = max(max_x, pos_x + Decimal(str(l_prev)))
                max_y = max(max_y, pos_y + Decimal(str(w_prev)))
                max_z = max(max_z, pos_z + Decimal(str(h_prev)))

            # Evaluate orientations to find one that fits at candidate positions
            placed = False
            for rot_l, rot_w, rot_h, lbl in rotations:
                # 1. Try placing along X axis
                if max_x + rot_l <= b_l and rot_w <= b_w and rot_h <= b_h:
                    position_x = max_x
                    position_y = Decimal('0.00')
                    position_z = Decimal('0.00')
                    strategy = Bin3DPlacement.PlacementStrategy.CORNER_ALIGN
                    selected_orientation = (rot_l, rot_w, rot_h)
                    label_dir = lbl
                    placed = True
                    break
                # 2. Try placing along Y axis
                if rot_l <= b_l and max_y + rot_w <= b_w and rot_h <= b_h:
                    position_x = Decimal('0.00')
                    position_y = max_y
                    position_z = Decimal('0.00')
                    strategy = Bin3DPlacement.PlacementStrategy.CORNER_ALIGN
                    selected_orientation = (rot_l, rot_w, rot_h)
                    label_dir = lbl
                    placed = True
                    break
                # 3. Try stacking along Z axis
                if rot_l <= b_l and rot_w <= b_w and max_z + rot_h <= b_h:
                    position_x = Decimal('0.00')
                    position_y = Decimal('0.00')
                    position_z = max_z
                    strategy = Bin3DPlacement.PlacementStrategy.STACKED
                    selected_orientation = (rot_l, rot_w, rot_h)
                    label_dir = lbl
                    placed = True
                    break

            if not placed:
                logger.warning("No space in bin for placement under 3D packing rules. Falling back to center placement.")
                position_x = Decimal('0.00')
                position_y = Decimal('0.00')
                position_z = max_z
                strategy = Bin3DPlacement.PlacementStrategy.STACKED
                selected_orientation = (p_l, p_w, p_h)
                label_dir = Bin3DPlacement.LabelDirection.FRONT
        # 5. Overwrite the BinAllocation's selected_orientation if it was recalculated to fit the layout
        if selected_orientation:
            parts = []
            for val in selected_orientation:
                f_val = float(val)
                if f_val.is_integer():
                    parts.append(str(int(f_val)))
                else:
                    parts.append(str(f_val))
            bin_allocation.selected_orientation = "x".join(parts)
            bin_allocation.save()

        # Update volumes including this item
        new_occupied_vol = occupied_vol + product_vol
        new_remaining_vol = bin_vol - new_occupied_vol
        util_pct = (new_occupied_vol / bin_vol) * 100

        # 6. Save and persist placement
        placement_3d, created = Bin3DPlacement.objects.update_or_create(
            bin_allocation=bin_allocation,
            defaults={
                'occupied_volume': new_occupied_vol,
                'remaining_volume': new_remaining_vol,
                'utilization_percentage': util_pct,
                'placement_strategy': strategy,
                'label_direction': label_dir,
                'position_x': position_x,
                'position_y': position_y,
                'position_z': position_z
            }
        )

        logger.info(
            "ThreeDOptimizationService: Created 3D Placement for Allocation %s at (%s, %s, %s) with strategy %s",
            bin_allocation.id, position_x, position_y, position_z, strategy
        )
        return placement_3d
