import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

RAG_ENDPOINT = "http://localhost:8001/api/rag/ingest"
TIMEOUT_SECONDS = 10

def send_to_rag(
    ocr_document_id: str,
    document_type: str = "OCRDocument",
    warehouse_id: Optional[str] = None,
    text: str = "",
    sku: Optional[str] = None,
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    zone: Optional[str] = None,
    rack: Optional[str] = None,
    shelf: Optional[str] = None,
    bin: Optional[str] = None,
) -> bool:
    """Send OCR text and metadata to the RAG ingestion endpoint.

    Returns True on success, False on any failure.
    """
    payload = {
        "ocr_document_id": str(ocr_document_id),
        "document_type": document_type,
        "warehouse_id": warehouse_id or "WH001",
        "text": text,
        "sku": sku,
        "product_id": product_id,
        "category": category,
        "zone": zone,
        "rack": rack,
        "shelf": shelf,
        "bin": bin,
    }
    try:
        response = requests.post(RAG_ENDPOINT, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        logger.info(
            "RAG ingestion succeeded for OCR document %s (status %s)",
            ocr_document_id,
            response.status_code,
        )
        return True
    except requests.RequestException as exc:
        logger.error(
            "RAG ingestion failed for OCR document %s: %s", ocr_document_id, str(exc)
        )
        return False
