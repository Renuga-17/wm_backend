import redis
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis_url = settings.CACHES['default']['LOCATION']
        self.client = None

    def connect(self):
        if not self.client:
            try:
                self.client = redis.Redis.from_url(self.redis_url)
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise e
        return self.client

    def set_key(self, key, value, ex=None):
        client = self.connect()
        try:
            return client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            return False

    def get_key(self, key):
        client = self.connect()
        try:
            val = client.get(key)
            return val.decode('utf-8') if val else None
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None
