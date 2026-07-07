import uuid
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.ai.services.rag_client import (
    RAGTimeoutException, RAGUnavailableException, RAGResponseException, RAGClient
)
from apps.ai.services.rag_query_service import RAGQueryService
from .serializers.rag_query_serializer import RAGQueryInputSerializer, RAGQueryOutputSerializer

logger = logging.getLogger(__name__)


class RAGQueryView(APIView):


    def post(self, request):
        request_id = str(uuid.uuid4())
        logger.info("RAGQueryView: Received query request [request_id=%s]", request_id)

        serializer = RAGQueryInputSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("RAGQueryView: Validation failed for request_id %s: %s", request_id, serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        query = validated_data.pop('query')
        filters = validated_data

        service = RAGQueryService()
        try:
            result = service.query_knowledge(
                query=query,
                user=request.user,
                filters=filters,
                request_id=request_id
            )

            output_data = {
                "request_id": request_id,
                "answer": result["answer"],
                "sources": result["sources"],
                "filters": result["filters"]
            }

            output_serializer = RAGQueryOutputSerializer(output_data)
            return Response(output_serializer.data, status=status.HTTP_200_OK)

        except RAGTimeoutException as e:
            logger.error("RAGQueryView: Timeout exception for request_id %s: %s", request_id, str(e))
            return Response(
                {"error": "RAG service request timed out.", "request_id": request_id},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except RAGUnavailableException as e:
            logger.error("RAGQueryView: Service unavailable exception for request_id %s: %s", request_id, str(e))
            return Response(
                {"error": "RAG service is currently unavailable.", "request_id": request_id},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except RAGResponseException as e:
            logger.error("RAGQueryView: Invalid response exception for request_id %s: %s", request_id, str(e))
            return Response(
                {"error": "RAG service returned an invalid response.", "request_id": request_id},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.exception("RAGQueryView: Unhandled error for request_id %s: %s", request_id, str(e))
            return Response(
                {"error": "An internal server error occurred.", "request_id": request_id},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RAGHealthView(APIView):
    permission_classes = []

    def get(self, request):
        client = RAGClient()
        is_healthy = client.ping()
        if is_healthy:
            return Response({"status": "healthy"}, status=status.HTTP_200_OK)
        return Response({"status": "unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
