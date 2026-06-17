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
        if not bin_allocation_id:
            return Response(
                {"error": "bin_allocation_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            bin_allocation = BinAllocation.objects.get(id=bin_allocation_id)
        except (BinAllocation.DoesNotExist, ValueError):
            logger.error("ThreeDPlacementView: BinAllocation not found with ID %s", bin_allocation_id)
            return Response(
                {"error": "Bin allocation not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        service = ThreeDOptimizationService()
        try:
            placement = service.evaluate_placement(bin_allocation)
            serializer = Bin3DPlacementSerializer(placement)
            logger.info("ThreeDPlacementView: Successfully generated 3D placement for allocation: %s", bin_allocation_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
