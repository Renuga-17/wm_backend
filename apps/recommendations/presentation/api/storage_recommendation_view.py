import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from ..serializers.storage_recommendation_serializer import (
    StorageRecommendationInputSerializer,
    StorageRecommendationOutputSerializer
)
from ...services.storage_recommendation_service import StorageRecommendationService

logger = logging.getLogger(__name__)

class StorageRecommendationView(APIView):
    """API endpoint to generate and retrieve storage recommendations.
    POST /api/recommendations/storage/
    """


    def post(self, request, *args, **kwargs):
        logger.info("StorageRecommendationView: POST request received with data: %s", request.data)
        serializer = StorageRecommendationInputSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error("StorageRecommendationView: Invalid request data: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        product_id = serializer.validated_data['product_id']
        service = StorageRecommendationService()
        try:
            recommendation = service.generate_recommendation(product_id)
            output_serializer = StorageRecommendationOutputSerializer(recommendation)
            logger.info("StorageRecommendationView: Successfully generated recommendation for product: %s", product_id)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            msg = str(e)
            logger.error("StorageRecommendationView: Validation error: %s", msg)
            if "not found" in msg.lower() or "does not exist" in msg.lower():
                return Response({"error": msg}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("StorageRecommendationView: Unexpected internal error: %s", str(e))
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
