from celery import shared_task
from .services.ocr_processing_service import OCRProcessingService


@shared_task
def process_ocr_document_task(document_id):
    service = OCRProcessingService()
    service.process_document(document_id)


@shared_task
def sync_rag_task(document_id):
    from apps.inbound.infrastructure.persistence.models import OCRDocument
    from apps.inbound.application.services.rag_service import sync_document_to_rag
    import logging
    logger = logging.getLogger(__name__)
    try:
        ocr_document = OCRDocument.objects.get(id=document_id)
        sync_document_to_rag(ocr_document)
    except Exception as e:
        logger.error("sync_rag_task: failed for document %s: %s", document_id, e)
