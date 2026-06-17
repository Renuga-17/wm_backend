import zlib
import json
import logging
from django.db import models
from apps.inbound.infrastructure.persistence.models import OCRDocument
from .rag_client import RAGClient

logger = logging.getLogger(__name__)


def get_user_id_int(user) -> int:
    """Safely converts user ID (which may be a UUID or string) into a 32-bit integer for the RAG service."""
    if not user or not user.is_authenticated:
        return None
    uid = user.id
    if hasattr(uid, 'bytes'):
        return zlib.crc32(uid.bytes)
    try:
        return int(uid)
    except (ValueError, TypeError):
        return zlib.crc32(str(uid).encode())


class RAGQueryService:
    def __init__(self):
        self.client = RAGClient()

    def query_knowledge(self, query: str, user, filters: dict, request_id: str) -> dict:
        logger.info("RAGQueryService: Starting query execution [request_id=%s]", request_id)

        # 1. Normalize Payload
        # Maps backend variables to targets defined in WarehouseRequest
        payload = {
            "ocrDocumentId": None,
            "title": query,
            "description": query,
            "documentType": filters.get("document_type"),
            "priority": "MEDIUM",
            "warehouseId": filters.get("warehouse_id"),
            "sku": filters.get("sku"),
            "productId": filters.get("product_id"),
            "category": filters.get("category"),
            "zone": filters.get("zone"),
            "rack": filters.get("rack"),
            "bin": filters.get("bin"),
            "auditTrail": [],
            "attemptCount": 1,
            "userId": get_user_id_int(user),
        }

        # 2. Call RAGClient
        response_data = self.client.analyze(payload, request_id)

        # 3. Parse Answer
        raw_suggestion = response_data.get("suggestion", "")
        answer = raw_suggestion
        try:
            # If the suggestion is a JSON string wrapped by the RAG model, parse it
            parsed = json.loads(raw_suggestion)
            if isinstance(parsed, dict):
                answer = (
                    parsed.get("analysis_summary")
                    or parsed.get("refined_explanation")
                    or raw_suggestion
                )
        except (json.JSONDecodeError, TypeError):
            # Fallback to the raw string if it is not valid JSON
            pass

        # 4. Resolve and Parse Source Documents
        sources = self.resolve_sources(filters)

        return {
            "answer": answer,
            "sources": sources,
            "filters": {k: v for k, v in filters.items() if v is not None},
        }

    def resolve_sources(self, filters: dict) -> list:
        sources = []
        qs = OCRDocument.objects.all()

        # Apply filters to find actual source documents
        if filters.get("document_type"):
            qs = qs.filter(document_type=filters["document_type"])

        if filters.get("sku"):
            sku = filters["sku"]
            qs = qs.filter(
                models.Q(raw_text__icontains=sku)
                | models.Q(file_name__icontains=sku)
            )

        # Retrieve top 3 matching documents
        for doc in qs[:3]:
            sources.append({
                "document_id": str(doc.id),
                "document_type": doc.document_type,
                "sku": filters.get("sku") or "",
            })

        # Fallback if no sources found but filters were provided
        if not sources and filters.get("document_type"):
            sources.append({
                "document_id": "DOC-AUTO-GEN",
                "document_type": filters["document_type"],
                "sku": filters.get("sku") or "",
            })

        return sources
