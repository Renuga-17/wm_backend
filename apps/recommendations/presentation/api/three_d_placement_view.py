import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from ...models.bin_allocation import BinAllocation
from ..serializers.bin_3d_placement_serializer import Bin3DPlacementSerializer
from ...services.three_d_optimization_service import ThreeDOptimizationService

logger = logging.getLogger(__name__)

class ThreeDPlacementView(APIView):
    """
    POST /api/recommendations/3d-placement/
    Evaluates 3D placement positioning for a completed BinAllocation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logger.info("ThreeDPlacementView: POST request received with data: %s", request.data)
        
        bin_allocation_id = request.data.get('bin_allocation_id')
        product_sku = request.data.get('product_sku')
        target_bin_code = request.data.get('target_bin_code')
        quantity = request.data.get('quantity')
        box_dimensions = request.data.get('box_dimensions')

        # Check if we have the frontend payload
        if product_sku and target_bin_code and quantity is not None and box_dimensions:
            # 1. Parse dimensions
            try:
                length, width, height = self.parse_dimensions(box_dimensions)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Look up product & bin
            from apps.inventory.infrastructure.persistence.models import Product, ProductDimension
            from apps.warehouse.models import Bin
            try:
                product = Product.objects.get(sku=product_sku)
            except Product.DoesNotExist:
                return Response({"error": f"Product with SKU '{product_sku}' not found"}, status=status.HTTP_404_NOT_FOUND)
            
            try:
                bin_obj = Bin.objects.get(bin_code=target_bin_code)
            except Bin.DoesNotExist:
                return Response({"error": f"Bin with code '{target_bin_code}' not found"}, status=status.HTTP_404_NOT_FOUND)

            # 3. Create or update ProductDimension
            ProductDimension.objects.update_or_create(
                product=product,
                defaults={
                    "length": length,
                    "width": width,
                    "height": height,
                    "box_length": length * 1.05,
                    "box_width": width * 1.05,
                    "box_height": height * 1.05
                }
            )

            # 4. Find or create BinAllocation
            from apps.recommendations.models.bin_allocation import BinAllocation
            shelf = bin_obj.shelf
            rack = shelf.rack
            zone = rack.zone
            zone_group = zone.zone_group
            if not zone_group:
                from apps.warehouse.models import ZoneGroup
                zone_group = ZoneGroup.objects.filter(warehouse=zone.warehouse).first()

            bin_allocation, created = BinAllocation.objects.get_or_create(
                product=product,
                bin=bin_obj,
                defaults={
                    "zone_group": zone_group,
                    "zone": zone,
                    "rack": rack,
                    "shelf": shelf,
                    "allocation_score": 100.0,
                    "allocation_reason": "Ad-hoc 3D placement request",
                    "selected_orientation": f"{length}x{width}x{height}",
                    "max_units": quantity,
                    "utilization_score": 0.0,
                }
            )
            if not created:
                bin_allocation.max_units = quantity
                bin_allocation.selected_orientation = f"{length}x{width}x{height}"
                bin_allocation.save()

        elif bin_allocation_id:
            from apps.recommendations.models.bin_allocation import BinAllocation
            try:
                bin_allocation = BinAllocation.objects.get(id=bin_allocation_id)
            except (BinAllocation.DoesNotExist, ValueError):
                logger.error("ThreeDPlacementView: BinAllocation not found with ID %s", bin_allocation_id)
                return Response(
                    {"error": "Bin allocation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Fetch dimensions from ProductDimension
            from apps.inventory.infrastructure.persistence.models import ProductDimension
            product_dim = ProductDimension.objects.filter(product=bin_allocation.product).first()
            if product_dim:
                length = float(product_dim.length)
                width = float(product_dim.width)
                height = float(product_dim.height)
            else:
                length = width = height = 0.0
            
            quantity = bin_allocation.max_units
            bin_obj = bin_allocation.bin
        else:
            return Response(
                {"error": "Either bin_allocation_id or (product_sku, target_bin_code, quantity, box_dimensions) must be provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. Evaluate placement
        service = ThreeDOptimizationService()
        try:
            placement = service.evaluate_placement(bin_allocation)
            
            # Compute real values based on real BE data
            max_units_fit = self.calculate_max_units_fit(bin_obj, length, width, height)
            bin_allocation.max_units = max_units_fit
            
            bin_vol = float(bin_obj.length * bin_obj.width * bin_obj.height)
            product_vol = float(length * width * height)
            if bin_vol > 0:
                bin_allocation.utilization_score = round((product_vol * quantity) / bin_vol, 4)
            else:
                bin_allocation.utilization_score = 0.0
                
            placement_strategy = getattr(placement, 'placement_strategy', 'BOTTOM_FLAT')
            bin_allocation.placement_instructions = f"Place {quantity} units of product in bin {bin_obj.bin_code} using {placement_strategy} strategy."
            bin_allocation.save()

            serializer = Bin3DPlacementSerializer(placement)
            response_data = serializer.data
            response_data['orientation'] = bin_allocation.selected_orientation
            response_data['max_units_fit'] = bin_allocation.max_units
            response_data['utilization_score'] = bin_allocation.utilization_score
            response_data['placement_instruction'] = bin_allocation.placement_instructions
            
            logger.info("ThreeDPlacementView: Successfully generated 3D placement for allocation: %s", bin_allocation.id)
            return Response(response_data, status=status.HTTP_200_OK if not bin_allocation_id else status.HTTP_201_CREATED)
        except ValueError as e:
            logger.error("ThreeDPlacementView: Validation/computation error: %s", str(e))
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("ThreeDPlacementView: Unexpected internal error: %s", str(e))
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def parse_dimensions(self, dim_str):
        import re
        matches = re.findall(r'(\d+(?:\.\d+)?)', dim_str)
        if len(matches) < 3:
            raise ValueError(f"Invalid dimensions format: '{dim_str}'. Must specify length, width, and height (e.g., '30x30x30').")
        return float(matches[0]), float(matches[1]), float(matches[2])

    def calculate_max_units_fit(self, bin_obj, length, width, height):
        rotations = [
            (length, width, height),
            (length, height, width),
            (width, length, height),
            (width, height, length),
            (height, length, width),
            (height, width, length),
        ]
        b_l, b_w, b_h = float(bin_obj.length), float(bin_obj.width), float(bin_obj.height)
        if b_l <= 0 or b_w <= 0 or b_h <= 0:
            return 0
            
        best_fit = 0
        for r_l, r_w, r_h in rotations:
            if r_l <= 0 or r_w <= 0 or r_h <= 0:
                continue
            fit_l = b_l // r_l
            fit_w = b_w // r_w
            fit_h = b_h // r_h
            units = int(fit_l * fit_w * fit_h)
            if units > best_fit:
                best_fit = units
        return best_fit
