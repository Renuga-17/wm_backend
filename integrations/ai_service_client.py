import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AIServiceClient:
    def __init__(self):
        self.config = settings.AI_SERVICE_SETTINGS
        self.base_url = self.config.get('BASE_URL')
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.config.get('API_KEY', '')
        }

    def get_storage_recommendation(self, product_data, warehouse_layout):
        url = f"{self.base_url}/api/v1/recommendations/placement"
        payload = {"product": product_data, "layout": warehouse_layout}
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Service placement request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommended_bin_id": None,
                "confidence_score": 0.0,
                "reasoning": "Fallback due to AI Service unavailability"
            }

    def get_slotting_optimization(self, zone_id):
        url = f"{self.base_url}/api/v1/recommendations/slotting"
        payload = {"zone_id": zone_id}
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Service slotting optimization request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "optimized_movements": [],
                "reasoning": "Fallback due to AI Service unavailability"
            }
