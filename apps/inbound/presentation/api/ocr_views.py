import logging
import hashlib
import sys
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.inbound.infrastructure.persistence.models import OCRDocument
from .ocr_serializers import OCRDocumentSerializer, OCRDocumentApprovalSerializer
from apps.inbound.application.services.rag_service import send_to_rag

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
        from ...tasks import process_ocr_document_task
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
        queryset = OCRDocument.objects.all().order_by('-created_at', '-id')
        
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
                "id": str(instance.id),
                "status": instance.processing_status,
                "processing_status": instance.processing_status,
                "document_type": instance.document_type,
                "confidence_score": instance.confidence_score,
                "raw_text": instance.raw_text,
                "extracted_json": instance.extracted_json,
                "file_name": instance.file_name,
                "file_path": instance.file_path,
                "rejection_reason": instance.rejection_reason,
                "error_message": instance.error_message,
                "created_at": instance.created_at,
                "updated_at": instance.updated_at,
                "rag_status": instance.rag_status,
                "rag_error_message": instance.rag_error_message,
                "chunk_count": instance.chunk_count,
                "warehouse_id": instance.warehouse_id,
                "sku": instance.sku,
                "product_id": instance.product_id,
                "category": instance.category,
                "zone": instance.zone,
                "rack": instance.rack,
                "shelf": instance.shelf,
                "bin": instance.bin
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("OCRDocumentViewSet: Retrieve failed: %s", e)
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='review-queue')
    def review_queue(self, request):
        """GET /api/ocr/review-queue/"""
        queryset = self.get_queryset().filter(processing_status=OCRDocument.ProcessingStatus.REVIEW_REQUIRED)
        page = self.paginate_queryset(queryset)
        
        def format_doc(doc):
            return {
                "id": str(doc.id),
                "document_type": doc.document_type,
                "confidence_score": doc.confidence_score,
                "processing_status": doc.processing_status,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            }

        if page is not None:
            data = [format_doc(doc) for doc in page]
            return self.get_paginated_response(data)
            
        data = [format_doc(doc) for doc in queryset]
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """POST /api/ocr/documents/{id}/approve/"""
        ocr_doc = self.get_object()
        

        initial_status = ocr_doc.processing_status
        if initial_status not in [
            OCRDocument.ProcessingStatus.REVIEW_REQUIRED,
            OCRDocument.ProcessingStatus.FAILED,
            OCRDocument.ProcessingStatus.COMPLETED,
            OCRDocument.ProcessingStatus.APPROVED,
        ]:
            return Response(
                {"error": f"Cannot approve document in status: {initial_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        custom_payload = request.data.get('extracted_json')
        if not custom_payload and 'extracted_data' in request.data:
            custom_payload = request.data
            
        if custom_payload:
            ocr_doc.extracted_json = custom_payload
            ocr_doc.save()

        # If document is already completed or approved, only run RAG sync
        if initial_status in [OCRDocument.ProcessingStatus.COMPLETED, OCRDocument.ProcessingStatus.APPROVED]:
            from apps.inbound.application.services.rag_service import sync_document_to_rag
            logger.info("Starting direct RAG sync")
            res = sync_document_to_rag(ocr_doc)
            if res.get("success"):
                logger.info("RAG ingestion succeeded")
                logger.info("Direct RAG sync completed")
                return Response({
                    "success": True,
                    "message": "OCR Document RAG sync triggered successfully (already processed).",
                    "document_id": str(ocr_doc.id),
                    "processing_status": ocr_doc.processing_status,
                }, status=status.HTTP_200_OK)
            else:
                logger.warning("Direct RAG sync failed: %s", res.get("error"))
                return Response(
                    {"error": f"RAG sync failed: {res.get('error', 'Unknown error')}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Update status to APPROVED
        ocr_doc.processing_status = OCRDocument.ProcessingStatus.APPROVED
        ocr_doc.save()

        # Orchestrate downstream ingestion
        from apps.inbound.application.services.inbound_orchestrator_service import InboundOrchestratorService
        orchestrator = InboundOrchestratorService()
        
        try:
            shipment = orchestrator.orchestrate_inbound(ocr_doc)
            return Response({
                "success": True,
                "message": "OCR Document approved and downstream ingestion completed successfully.",
                "document_id": str(ocr_doc.id),
                "processing_status": ocr_doc.processing_status,
                "shipment_code": shipment.shipment_code
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Orchestrator failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """POST /api/ocr/documents/{id}/reject/"""
        ocr_doc = self.get_object()
        
        # If already rejected, return success directly (idempotent behavior)
        if ocr_doc.processing_status == OCRDocument.ProcessingStatus.REJECTED:
            return Response({
                "success": True,
                "message": "OCR Document is already rejected.",
                "document_id": str(ocr_doc.id),
                "processing_status": ocr_doc.processing_status
            }, status=status.HTTP_200_OK)
            
        if ocr_doc.processing_status not in [OCRDocument.ProcessingStatus.REVIEW_REQUIRED, OCRDocument.ProcessingStatus.FAILED]:
            return Response(
                {"error": f"Cannot reject document in status: {ocr_doc.processing_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        reason = request.data.get('reason')
        if not reason:
            return Response({"error": "reason is required"}, status=status.HTTP_400_BAD_REQUEST)

        ocr_doc.processing_status = OCRDocument.ProcessingStatus.REJECTED
        ocr_doc.rejection_reason = reason
        ocr_doc.save()
        
        return Response({
            "success": True,
            "message": "OCR Document rejected successfully.",
            "document_id": str(ocr_doc.id),
            "processing_status": ocr_doc.processing_status
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='sync-rag')
    def sync_rag(self, request, pk=None):
        """POST /api/ocr/documents/{id}/sync-rag/"""
        ocr_doc = self.get_object()
        
        if ocr_doc.processing_status not in [OCRDocument.ProcessingStatus.COMPLETED, OCRDocument.ProcessingStatus.APPROVED]:
            return Response(
                {"error": f"Cannot sync to RAG for document in status: {ocr_doc.processing_status}. Document must be COMPLETED or APPROVED."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        from apps.inbound.application.services.rag_service import sync_document_to_rag
        
        res = sync_document_to_rag(ocr_doc)
        if res.get("success"):
            return Response({
                "success": True,
                "message": "OCR Document successfully synced to RAG."
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": f"Failed to sync document to RAG: {res.get('error', 'Unknown error')}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RAGRetryView(APIView):
    """
    POST /api/rag/retry/{document_id}
    Retries RAG ingestion for a document. Does not re-run OCR.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, document_id, *args, **kwargs):
        try:
            ocr_doc = OCRDocument.objects.get(id=document_id)
        except (OCRDocument.DoesNotExist, ValueError):
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        if ocr_doc.processing_status not in [OCRDocument.ProcessingStatus.COMPLETED, OCRDocument.ProcessingStatus.APPROVED]:
            return Response(
                {"error": f"Cannot retry RAG ingestion. OCR must be COMPLETED or APPROVED (current status: {ocr_doc.processing_status})"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set status to INGESTING
        ocr_doc.rag_status = "INGESTING"
        ocr_doc.save()

        try:
            res = send_to_rag(
                ocr_document_id=str(ocr_doc.id),
                document_type=ocr_doc.document_type or "OCRDocument",
                warehouse_id=ocr_doc.warehouse_id or "WH001",
                text=ocr_doc.raw_text,
                sku=ocr_doc.sku,
                product_id=ocr_doc.product_id,
                category=ocr_doc.category,
                zone=ocr_doc.zone,
                rack=ocr_doc.rack,
                shelf=ocr_doc.shelf,
                bin=ocr_doc.bin,
            )
            if res.get("success"):
                ocr_doc.rag_status = "INGESTED"
                ocr_doc.chunk_count = res.get("chunks_created", 0)
                ocr_doc.rag_error_message = None
                ocr_doc.save()
                return Response({
                    "success": True,
                    "message": "RAG ingestion retry completed successfully.",
                    "document_id": str(ocr_doc.id),
                    "rag_status": ocr_doc.rag_status,
                    "chunk_count": ocr_doc.chunk_count
                }, status=status.HTTP_200_OK)
            else:
                ocr_doc.rag_status = "FAILED"
                ocr_doc.rag_error_message = res.get("error", "Unknown ingestion error")
                ocr_doc.save()
                return Response({
                    "success": False,
                    "error": ocr_doc.rag_error_message,
                    "rag_status": ocr_doc.rag_status
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("RAGRetryView: Retry failed: %s", e)
            ocr_doc.rag_status = "FAILED"
            ocr_doc.rag_error_message = str(e)
            ocr_doc.save()
            return Response({
                "success": False,
                "error": str(e),
                "rag_status": ocr_doc.rag_status
            }, status=status.HTTP_400_BAD_REQUEST)

