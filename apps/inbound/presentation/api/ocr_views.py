import logging
import hashlib
import sys
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.inbound.infrastructure.persistence.models import OCRDocument
from .ocr_serializers import OCRDocumentSerializer
from ...tasks import process_ocr_document_task

logger = logging.getLogger(__name__)


class OCRUploadView(APIView):
    """
    POST /api/ocr/upload/
    Accepts a document file via multipart/form-data. Calculates hash to detect
    duplicates, creates OCRDocument record, and triggers OCR pipeline.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logger.info("OCRUploadView: Upload request received.")
        file_obj = request.FILES.get('file')
        if not file_obj:
            logger.error("OCRUploadView: No file found in request.")
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Calculate SHA256 hash of the uploaded file
        try:
            sha256 = hashlib.sha256()
            for chunk in file_obj.chunks():
                sha256.update(chunk)
            doc_hash = sha256.hexdigest()
        except Exception as e:
            logger.error("OCRUploadView: Hash calculation failed: %s", e)
            return Response({"error": f"Failed to compute file hash: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Duplicate Detection (Phase 4)
        existing_doc = OCRDocument.objects.filter(document_hash=doc_hash).first()
        if existing_doc:
            logger.info("OCRUploadView: Duplicate document found with hash %s (ID: %s)", doc_hash, existing_doc.id)
            return Response({
                "document_id": str(existing_doc.id),
                "status": existing_doc.processing_status
            }, status=status.HTTP_200_OK)

        # 3. Save file to media storage
        try:
            saved_path = default_storage.save(f"ocr_documents/{file_obj.name}", file_obj)
        except Exception as e:
            logger.error("OCRUploadView: File save failed: %s", e)
            return Response({"error": f"Failed to save file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 4. Create OCRDocument in UPLOADED status
        document_type = request.data.get('document_type') or 'invoice'
        ocr_doc = OCRDocument.objects.create(
            file_name=file_obj.name,
            file_path=saved_path,
            document_type=document_type,
            document_hash=doc_hash,
            processing_status=OCRDocument.ProcessingStatus.UPLOADED
        )
        logger.info("OCRUploadView: Created OCRDocument %s", ocr_doc.id)

        # 5. Trigger OCR processing (Phase 3 & 5)
        is_testing = 'test' in sys.argv or 'pytest' in sys.modules
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False) or is_testing:
            logger.info("OCRUploadView: Triggering OCR processing synchronously (test/eager mode).")
            process_ocr_document_task(str(ocr_doc.id))
            ocr_doc.refresh_from_db()
            resp_status = ocr_doc.processing_status
        else:
            logger.info("OCRUploadView: Triggering OCR processing asynchronously.")
            process_ocr_document_task.delay(str(ocr_doc.id))
            resp_status = OCRDocument.ProcessingStatus.UPLOADED

        return Response({
            "document_id": str(ocr_doc.id),
            "status": resp_status
        }, status=status.HTTP_201_CREATED)


class OCRDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for OCRDocument retrieval and history tracking.
    GET /api/ocr/documents/        - list paginated audit log
    GET /api/ocr/documents/{id}/   - check document status & details
    """
    serializer_class = OCRDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = OCRDocument.objects.all().order_by('-created_at')
        
        # Filtering (Phase 8)
        status_filter = self.request.query_params.get('status')
        type_filter = self.request.query_params.get('document_type')
        
        if status_filter:
            queryset = queryset.filter(processing_status=status_filter)
        if type_filter:
            queryset = queryset.filter(document_type=type_filter)
            
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """GET /api/ocr/documents/{id}/ -> Status API (Phase 7)"""
        try:
            instance = self.get_object()
            return Response({
                "document_id": str(instance.id),
                "status": instance.processing_status,
                "document_type": instance.document_type,
                "confidence_score": instance.confidence_score
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("OCRDocumentViewSet: Retrieve failed: %s", e)
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)
