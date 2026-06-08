import logging
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from integrations.ocr_service_client import OCRServiceClient
from apps.inbound.infrastructure.persistence.models import OCRDocument
from .serializers import OCRDocumentSerializer
from apps.inbound.application.services.rag_service import send_to_rag

logger = logging.getLogger(__name__)


class OCRExtractView(APIView):
    """
    POST /api/ocr/extract/

    Submit a document URL for OCR extraction.
    The document record is created, the OCR microservice is called
    synchronously, and the result is stored before returning the response.

    Request body:
        {
            "document_name": "Supplier Invoice Jan 2026",
            "document_type": "invoice",
            "document_url": "https://example.com/invoice.pdf"
        }
    """

    def post(self, request):
        serializer = OCRDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create the record with PROCESSING status
        document = serializer.save(status=OCRDocument.Status.PROCESSING)

        # Call OCR microservice synchronously
        client = OCRServiceClient()
        ocr_response = client.extract_text(document.document_url)

        if ocr_response['success']:
            document.extracted_text = ocr_response['result']
            document.status = OCRDocument.Status.COMPLETED
            document.error_message = None
            logger.info(f"OCR extraction completed for document {document.id}")
        else:
            document.status = OCRDocument.Status.FAILED
            document.error_message = ocr_response['error']
            logger.error(
                f"OCR extraction failed for document {document.id}: {ocr_response['error']}"
            )

        document.save()
        # Trigger RAG ingestion after saving the OCR document
        send_to_rag(
            ocr_document_id=str(document.id),
            document_type="OCRDocument",
            warehouse_id="WH001",
            text=document.extracted_text or "",
        )

        response_serializer = OCRDocumentSerializer(document)
        http_status = (
            status.HTTP_200_OK
            if ocr_response['success']
            else status.HTTP_502_BAD_GATEWAY
        )
        return Response(response_serializer.data, status=http_status)


class OCRHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/ocr/history/        - List all OCR extractions (paginated)
    GET /api/ocr/history/{id}/   - Retrieve a specific OCR result
    """
    queryset = OCRDocument.objects.all()
    serializer_class = OCRDocumentSerializer
