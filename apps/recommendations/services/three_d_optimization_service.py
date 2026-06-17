import logging
from decimal import Decimal
from apps.warehouse.models import Bin
from apps.inventory.infrastructure.persistence.models import Product, ProductDimension
from ..models.bin_allocation import BinAllocation
from ..models.bin_3d_placement import Bin3DPlacement

logger = logging.getLogger(__name__)

class ThreeDOptimizationService:
    def evaluate_placement(self, bin_allocation: BinAllocation) -> Bin3DPlacement:
        """
        Main method to evaluate and persist 3D placement for a completed BinAllocation.
        """
        logger.info("ThreeDOptimizationService: Evaluating 3D placement for allocation %s", bin_allocation.id)
        
        product = bin_allocation.product
        bin_obj = bin_allocation.bin

        # 1. Get ProductDimension
        product_dim = ProductDimension.objects.filter(product=product).first()
        if not product_dim:
            logger.error("ThreeDOptimizationService: ProductDimension not found for product %s", product.sku)
            raise ValueError("Product dimensions not found")

        # 2. Get existing placements in the same bin (excluding the current one)
        existing_placements = Bin3DPlacement.objects.filter(
            bin_allocation__bin=bin_obj
        ).exclude(bin_allocation=bin_allocation)

        # 3. Calculate volumes
        bin_vol = Decimal(str(bin_obj.length)) * Decimal(str(bin_obj.width)) * Decimal(str(bin_obj.height))
        product_vol = Decimal(str(product_dim.length)) * Decimal(str(product_dim.width)) * Decimal(str(product_dim.height))
        
        occupied_vol = Decimal('0.00')
        for placement in existing_placements:
            alloc = placement.bin_allocation
            try:
                l, w, h = map(float, alloc.selected_orientation.split('x'))
                occupied_vol += Decimal(str(l)) * Decimal(str(w)) * Decimal(str(h))
            except Exception:
                # Fallback if selected_orientation parsing fails
                dim = ProductDimension.objects.filter(product=alloc.product).first()
                if dim:
                    occupied_vol += Decimal(str(dim.length)) * Decimal(str(dim.width)) * Decimal(str(dim.height))

        # Check total remaining volume
        remaining_vol = bin_vol - occupied_vol
        
        # 4. Evaluate orientations
        p_l = Decimal(str(product_dim.length))
        p_w = Decimal(str(product_dim.width))
        p_h = Decimal(str(product_dim.height))

        b_l = Decimal(str(bin_obj.length))
        b_w = Decimal(str(bin_obj.width))
        b_h = Decimal(str(bin_obj.height))

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
                    l_prev, w_prev, h_prev = float(product_dim.length), float(product_dim.width), float(product_dim.height)
                
                max_x = max(max_x, p.position_x + Decimal(str(l_prev)))
                max_y = max(max_y, p.position_y + Decimal(str(w_prev)))
                max_z = max(max_z, p.position_z + Decimal(str(h_prev)))

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
                raise ValueError("No space in bin for placement under 3D packing rules")

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
