from celery import shared_task
from .services.ocr_processing_service import OCRProcessingService


@shared_task
def process_ocr_document_task(document_id):
    service = OCRProcessingService()
    service.process_document(document_id)
