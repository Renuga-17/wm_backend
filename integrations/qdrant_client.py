from qdrant_client import QdrantClient as PyQdrantClient
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

    def search_similar_vectors(self, collection_name, query_vector, limit=5):
        client = self.connect()
        try:
            return client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Qdrant vector search failed: {e}")
            return []
