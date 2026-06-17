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

    def analyze_layout(self, file_path, file_type):
        url = f"{self.base_url}/api/v1/layout/analyze"
        try:
            import os
            # Omit Content-Type from headers for multipart uploads so requests sets the boundary
            multipart_headers = {
                'X-API-Key': self.config.get('API_KEY', '')
            }
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                data = {'file_type': file_type}
                response = requests.post(url, files=files, data=data, headers=multipart_headers, timeout=30)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"AI Service layout analysis request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "entities": []
            }

    def generate_navigation_guidance(self, route_data: dict) -> dict:
        url = f"{self.base_url}/api/v1/guidance/navigation"
        try:
            response = requests.post(url, json=route_data, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Service navigation instructions fallback request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "instructions": "Fallback: Proceed along the calculated route."
            }

    def generate_placement_guidance(self, placement_context: dict) -> dict:
        url = f"{self.base_url}/api/v1/guidance/placement"
        try:
            response = requests.post(url, json=placement_context, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Service placement instructions fallback request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "instructions": "Fallback: Place product flat in the allocated bin."
            }


