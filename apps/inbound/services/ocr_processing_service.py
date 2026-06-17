import logging
import traceback
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from apps.inbound.infrastructure.persistence.models import OCRDocument, InboundShipment
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, ProductDimension
from apps.recommendations.models.product_classification import ProductClassification
from apps.recommendations.models.recommendation_rule import RecommendationRule
from apps.recommendations.services.storage_recommendation_service import StorageRecommendationService
from apps.recommendations.services.bin_allocation_service import BinAllocationService
from apps.recommendations.services.three_d_optimization_service import ThreeDOptimizationService
from apps.warehouse.application.services.route_optimizer import RouteOptimizer
from apps.warehouse.infrastructure.persistence.models import NavigationNode
from .ocr_client import OCRClient, OCRClientException

logger = logging.getLogger(__name__)


class OCRProcessingService:
    def __init__(self):
        self.client = OCRClient()

    def process_document(self, document_id) -> None:
        """Processes the OCRDocument: calls the OCR service, stores the results,
        and triggers the downstream WMS ingestion pipeline (Inbound, Products, Recommendations,
        Allocations, 3D Placements, and Routes).
        """
        logger.info("OCRProcessingService: Starting processing for document ID: %s", document_id)
        try:
            ocr_doc = OCRDocument.objects.get(id=document_id)
        except OCRDocument.DoesNotExist:
            logger.error("OCRProcessingService: Document ID %s not found.", document_id)
            return

        # 1. Update status to PROCESSING
        ocr_doc.processing_status = OCRDocument.ProcessingStatus.PROCESSING
        ocr_doc.save()

        # 2. Call OCR microservice
        try:
            # Read file bytes
            file_full_path = ocr_doc.file_path
            # Since files are saved via default_storage, we open the file
            from django.core.files.storage import default_storage
            with default_storage.open(file_full_path, 'rb') as f:
                file_bytes = f.read()

            ocr_res = self.client.extract_document(
                file_bytes=file_bytes,
                file_name=ocr_doc.file_name,
                content_type='application/pdf' if ocr_doc.file_name.lower().endswith('.pdf') else 'image/png'
            )
        except Exception as e:
            logger.error("OCRProcessingService: OCR client failed: %s", e)
            ocr_doc.processing_status = OCRDocument.ProcessingStatus.FAILED
            ocr_doc.error_message = str(e)
            ocr_doc.save()
            return

        # 3. Parse responses
        raw_text = ocr_res.get('raw_text', '')
        extracted_data = ocr_res.get('extracted_data', {})
        confidence_score = ocr_res.get('confidence_score', 0.0)
        doc_type = ocr_res.get('document_type') or ocr_doc.document_type or 'invoice'

        # Store raw text and extracted JSON on the document
        ocr_doc.raw_text = raw_text
        ocr_doc.extracted_json = ocr_res
        ocr_doc.confidence_score = confidence_score
        ocr_doc.document_type = doc_type

        # 4. Review queue logic (Phase 6): check confidence score
        if confidence_score < 0.85:
            ocr_doc.processing_status = OCRDocument.ProcessingStatus.REVIEW_REQUIRED
            ocr_doc.save()
            logger.warning("OCRProcessingService: Confidence score %.2f is below threshold. Review required.", confidence_score)
            return

        # 5. Domain WMS objects creation via InboundOrchestratorService
        from apps.inbound.application.services.inbound_orchestrator_service import InboundOrchestratorService
        orchestrator = InboundOrchestratorService()
        try:
            orchestrator.orchestrate_inbound(ocr_doc)
        except Exception as err:
            logger.error("OCRProcessingService: Downstream ingestion pipeline failed: %s", err)
