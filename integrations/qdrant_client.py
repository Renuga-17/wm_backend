from qdrant_client import QdrantClient as PyQdrantClient
from qdrant_client.http import models
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class QdrantClientWrapper:
    def __init__(self):
        self.config = settings.QDRANT_SETTINGS
        self.client = None

    def connect(self):
        if not self.client:
            try:
                self.client = PyQdrantClient(
                    url=self.config.get('URL'),
                    api_key=self.config.get('API_KEY') or None
                )
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}")
                raise e
        return self.client

    def ensure_collection(self, collection_name, vector_size):
        client = self.connect()
        if not client.collection_exists(collection_name):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
            # Create payload indexes; ignore errors if already exist
            for field in ["metadata.document_type", "metadata.warehouse_id", "metadata.ocr_document_id"]:
                try:
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field,
                        field_schema=models.PayloadSchemaType.KEYWORD,
                    )
                except Exception as e:
                    logger.debug(f"Payload index for {field} may already exist or failed: {e}")
        # If collection exists, ensure indexes exist (idempotent check)
        else:
            for field in ["metadata.document_type", "metadata.warehouse_id", "metadata.ocr_document_id"]:
                try:
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field,
                        field_schema=models.PayloadSchemaType.KEYWORD,
                    )
                except Exception:
                    pass
