import logging
import requests
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

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
    
    base_url = getattr(settings, 'RAG_BASE_URL', 'http://localhost:8002').rstrip('/')
    endpoint = f"{base_url}/api/rag/ingest"
    timeout = getattr(settings, 'RAG_TIMEOUT', TIMEOUT_SECONDS)
    
    logger.info("Sending POST request to RAG endpoint: %s with payload: %s", endpoint, payload)
    
    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        chunks_created = data.get("chunks_created", 0)
        logger.info(
            "RAG ingestion succeeded for OCR document %s (status %s, chunks %s). Response: %s",
            ocr_document_id,
            response.status_code,
            chunks_created,
            data,
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
            "RAG ingestion failed at endpoint %s for OCR document %s. Response status: %s. Error: %s",
            endpoint,
            ocr_document_id,
            exc.response.status_code if exc.response is not None else "N/A",
            error_msg
        )
        return {"success": False, "error": error_msg}
    except Exception as exc:
        logger.error(
            "RAG ingestion failed at endpoint %s for OCR document %s: %s",
            endpoint,
            ocr_document_id,
            exc
        )
        return {"success": False, "error": str(exc)}


def sync_document_to_rag(ocr_document) -> dict:
    """Extract WMS metadata for the OCR Document and send it to RAG, updating database status."""
    logger.info("sync_document_to_rag: Extracting metadata for OCR Document %s", ocr_document.id)
    
    # Update status to INGESTING
    ocr_document.rag_status = "INGESTING"
    ocr_document.save()
    
    sku = None
    product_id = None
    category = None
    
    from apps.warehouse.infrastructure.persistence.models import Warehouse
    warehouse = Warehouse.objects.first()
    warehouse_id = str(warehouse.id) if warehouse else "WH001"
    
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
                allocation = BinAllocation.objects.filter(product=product).select_related(
                    'zone',
                    'rack',
                    'shelf',
                    'bin'
                ).first()
                if allocation:
                    warehouse_id = str(allocation.zone.warehouse_id)
                    zone = allocation.zone.zone_name
                    rack = allocation.rack.rack_code
                    shelf = str(allocation.shelf.shelf_number)
                    bin_code = allocation.bin.bin_code
                break  # Standard representative product
    except Exception as e:
        logger.warning("sync_document_to_rag: WMS metadata extraction failed: %s", e)

    try:
        res = send_to_rag(
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
        
        if res.get("success"):
            ocr_document.rag_status = "INGESTED"
            ocr_document.chunk_count = res.get("chunks_created", 0)
            ocr_document.rag_error_message = None
        else:
            ocr_document.rag_status = "FAILED"
            ocr_document.rag_error_message = res.get("error", "Unknown ingestion error")
        ocr_document.save()
        return res
    except Exception as exc:
        logger.error("sync_document_to_rag: RAG ingestion trigger failed: %s", exc)
        ocr_document.rag_status = "FAILED"
        ocr_document.rag_error_message = str(exc)
        ocr_document.save()
        return {"success": False, "error": str(exc)}
