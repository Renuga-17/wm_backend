import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from ..serializers.bin_allocation_serializer import (
    BinAllocationInputSerializer,
    BinAllocationOutputSerializer
)
from ...services.bin_allocation_service import (
    BinAllocationService,
    ProductNotFoundError,
    RecommendationNotFoundError,
    DimensionsNotFoundError,
    AllocationFailedError
)

logger = logging.getLogger(__name__)

class BinAllocationView(APIView):
    """API endpoint to select and allocate a bin for a product.
    POST /api/recommendations/bin-allocation/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logger.info("BinAllocationView: POST request received with data: %s", request.data)
        serializer = BinAllocationInputSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error("BinAllocationView: Invalid request data: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data['product_id']
        service = BinAllocationService()

        try:
            allocation = service.generate_bin_allocation(product_id)
            output_serializer = BinAllocationOutputSerializer(allocation)
            logger.info("BinAllocationView: Successfully allocated bin for product: %s", product_id)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            
        except ProductNotFoundError as e:
            logger.error("BinAllocationView: Product not found: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
            
        except RecommendationNotFoundError as e:
            logger.error("BinAllocationView: Storage recommendation not found: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
            
        except DimensionsNotFoundError as e:
            logger.error("BinAllocationView: Product dimensions not found: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except AllocationFailedError as e:
            logger.error("BinAllocationView: Allocation failed: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.exception("BinAllocationView: Unexpected internal error: %s", str(e))
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
