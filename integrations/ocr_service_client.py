import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class OCRServiceClient:
    def __init__(self):
        self.config = settings.OCR_SERVICE_SETTINGS
        self.base_url = self.config.get('BASE_URL')
        self.headers = {
            'Content-Type': 'application/json',
        }

    def extract_text(self, url: str) -> dict:
        """
        Send a PDF URL to the OCR microservice and return extracted text.

        Args:
            url: The publicly accessible URL of the PDF document.

        Returns:
            dict with keys:
                - success (bool)
                - result (str): extracted text on success, empty string on failure
                - error (str): error message on failure, empty string on success
        """
        endpoint = f"{self.base_url}/extract"
        payload = {"url": url}
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return {
                "success": True,
                "result": data.get("result", ""),
                "error": "",
            }
        except requests.exceptions.Timeout:
            logger.error(f"OCR Service request timed out for URL: {url}")
            return {
                "success": False,
                "result": "",
                "error": "OCR service request timed out.",
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"OCR Service HTTP error for URL {url}: {e}")
            return {
                "success": False,
                "result": "",
                "error": f"OCR service returned HTTP error: {e}",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"OCR Service request failed for URL {url}: {e}")
            return {
                "success": False,
                "result": "",
                "error": str(e),
            }
