import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

from django.conf import settings

RAG_BASE_URL = getattr(settings, 'RAG_BASE_URL', 'http://localhost:8002').rstrip('/')
RAG_ENDPOINT = f"{RAG_BASE_URL}/api/rag/ingest"
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
) -> dict:
    """Send OCR text and metadata to the RAG ingestion endpoint.

    Returns a dict with success, chunks_created, and error details.
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
        data = response.json()
        chunks_created = data.get("chunks_created", 0)
        logger.info(
            "RAG ingestion succeeded for OCR document %s (status %s, chunks %s)",
            ocr_document_id,
            response.status_code,
            chunks_created,
        )
        return {"success": True, "chunks_created": chunks_created}
    except requests.RequestException as exc:
        error_msg = str(exc)
        if exc.response is not None:
            try:
                error_msg = exc.response.json().get("detail", error_msg)
            except Exception:
                error_msg = exc.response.text or error_msg
        logger.error(
            "RAG ingestion failed for OCR document %s: %s", ocr_document_id, error_msg
        )
        return {"success": False, "error": error_msg}
