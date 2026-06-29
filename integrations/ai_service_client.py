import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
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
        # Create a session with retry strategy for transient network errors
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        # Pre‑flight health check
        self.service_available = self._check_service_health()

    def _check_service_health(self) -> bool:
        """Ping the AI service health endpoint.
        Returns True if the service responds with a 2xx status, else False.
        """
        import sys
        is_testing = 'test' in sys.argv or 'pytest' in sys.modules
        if is_testing:
            return False
            
        for path in ["/health", "/"]:
            health_url = f"{self.base_url.rstrip('/')}{path}"
            try:
                resp = self.session.get(health_url, timeout=3)
                if resp.ok:
                    logger.info(f"AI Service health check succeeded on {path}.")
                    return True
            except Exception:
                pass
        logger.warning("AI Service health check failed on all endpoints.")
        return False

    def _ensure_service(self) -> bool:
        """Ensure the service is reachable; attempt a quick re‑check if previously unavailable."""
        if not self.service_available:
            self.service_available = self._check_service_health()
        return self.service_available


    def get_storage_recommendation(self, product_data, warehouse_layout):
        if not self._ensure_service():
            return {
                "success": False,
                "error": "AI Service unavailable",
                "recommended_bin_id": None,
                "confidence_score": 0.0,
                "reasoning": "Fallback due to AI Service unavailability"
            }

        url = f"{self.base_url}/api/v1/recommendations/placement"
        payload = {"product": product_data, "layout": warehouse_layout}
        try:
            response = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Service placement request failed: {e}")
            # Mark service as down for subsequent calls
            self.service_available = False
            return {
                "success": False,
                "error": str(e),
                "recommended_bin_id": None,
                "confidence_score": 0.0,
                "reasoning": "Fallback due to AI Service unavailability"
            }

    def get_slotting_optimization(self, zone_id):
        if not self._ensure_service():
            return {
                "success": False,
                "error": "AI Service unavailable",
                "optimized_movements": [],
                "reasoning": "Fallback due to AI Service unavailability"
            }

        url = f"{self.base_url}/api/v1/recommendations/slotting"
        payload = {"zone_id": zone_id}
        try:
            response = self.session.post(url, json=payload, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Service slotting optimization request failed: {e}")
            self.service_available = False
            return {
                "success": False,
                "error": str(e),
                "optimized_movements": [],
                "reasoning": "Fallback due to AI Service unavailability"
            }

    def analyze_layout(self, file_path, file_type):
        if not self._ensure_service():
            return {
                "success": False,
                "error": "AI Service unavailable",
                "entities": []
            }

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
                response = self.session.post(url, files=files, data=data, headers=multipart_headers, timeout=30)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"AI Service layout analysis request failed: {e}")
            self.service_available = False
            return {
                "success": False,
                "error": str(e),
                "entities": []
            }

    def generate_navigation_guidance(self, route_data: dict) -> dict:
        if not self._ensure_service():
            return {
                "success": False,
                "error": "AI Service unavailable",
                "instructions": "Fallback: Proceed along the calculated route."
            }

        url = f"{self.base_url}/api/v1/guidance/navigation"
        try:
            response = self.session.post(url, json=route_data, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Service navigation instructions fallback request failed: {e}")
            self.service_available = False
            return {
                "success": False,
                "error": str(e),
                "instructions": "Fallback: Proceed along the calculated route."
            }

    def generate_placement_guidance(self, placement_context: dict) -> dict:
        if not self._ensure_service():
            return {
                "success": False,
                "error": "AI Service unavailable",
                "instructions": "Fallback: Place product flat in the allocated bin."
            }

        url = f"{self.base_url}/api/v1/guidance/placement"
        try:
            response = self.session.post(url, json=placement_context, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Service placement instructions fallback request failed: {e}")
            self.service_available = False
            return {
                "success": False,
                "error": str(e),
                "instructions": "Fallback: Place product flat in the allocated bin."
            }


