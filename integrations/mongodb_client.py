from pymongo import MongoClient
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self):
        self.config = settings.MONGODB_SETTINGS
        self.client = None
        self.db = None

    def connect(self):
        if not self.client:
            try:
                self.client = MongoClient(self.config.get('URI'))
                self.db = self.client[self.config.get('DB_NAME')]
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise e
        return self.db

    def get_collection(self, collection_name):
        db = self.connect()
        return db[collection_name]
