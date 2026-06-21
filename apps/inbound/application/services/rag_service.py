import logging
import requests
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

RAG_ENDPOINT = "http://localhost:8002/api/rag/ingest"
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
    
    base_url = getattr(settings, 'RAG_BASE_URL', 'http://localhost:8002').rstrip('/')
    endpoint = f"{base_url}/api/rag/ingest"
    timeout = getattr(settings, 'RAG_TIMEOUT', TIMEOUT_SECONDS)
    
    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        logger.info(
            "RAG ingestion succeeded for OCR document %s (status %s)",
            ocr_document_id,
            response.status_code,
        )
        return True
    except Exception as exc:
        logger.error(
            "RAG ingestion failed for OCR document %s: %s", ocr_document_id, str(exc)
        )
        return False


def sync_document_to_rag(ocr_document) -> bool:
    """Extract WMS metadata for the OCR Document and send it to RAG."""
    logger.info("sync_document_to_rag: Extracting metadata for OCR Document %s", ocr_document.id)
    
    sku = None
    product_id = None
    category = None
    warehouse_id = "WH001"
    zone = None
    rack = None
    shelf = None
    bin_code = None

    try:
        payload = ocr_document.extracted_json or {}
        extracted_data = payload.get('extracted_data', {})
        products_list = extracted_data.get('products', [])
        if not products_list:
            products_list = payload.get('storage_payloads', {}).get('product_payload', [])

        from apps.inventory.infrastructure.persistence.models import Product
        from apps.recommendations.models.bin_allocation import BinAllocation

        for prod_item in products_list:
            item_sku = prod_item.get('sku')
            if not item_sku:
                continue

            product = Product.objects.filter(sku=item_sku).first()
            if product:
                sku = item_sku
                product_id = str(product.id)
                category = product.category.category_name if product.category else None
                
                # Fetch the latest allocation for this product
                allocation = BinAllocation.objects.filter(product=product).first()
                if allocation:
                    warehouse_id = str(allocation.zone.warehouse_id)
                    zone = allocation.zone.zone_name
                    rack = allocation.rack.rack_code
                    shelf = str(allocation.shelf.shelf_number)
                    bin_code = allocation.bin.bin_code
                break  # Standard representative product
    except Exception as e:
        logger.warning("sync_document_to_rag: WMS metadata extraction failed: %s", e)

    return send_to_rag(
        ocr_document_id=str(ocr_document.id),
        document_type="OCRDocument",
        warehouse_id=warehouse_id,
        text=ocr_document.raw_text,
        sku=sku,
        product_id=product_id,
        category=category,
        zone=zone,
        rack=rack,
        shelf=shelf,
        bin=bin_code,
    )
