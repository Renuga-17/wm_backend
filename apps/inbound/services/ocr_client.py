import os
import requests
import logging

logger = logging.getLogger(__name__)


class OCRClientException(Exception):
    pass


class OCRClient:
    def __init__(self):
        self.url = os.getenv('OCR_SERVICE_URL', 'http://localhost:8001').rstrip('/')
        try:
            self.timeout = int(os.getenv('OCR_TIMEOUT', '60'))
        except ValueError:
            self.timeout = 60

    def extract_document(self, file_bytes: bytes, file_name: str, content_type: str = 'application/octet-stream') -> dict:
        endpoint = f"{self.url}/api/v1/ocr/extract"
        files = {
            'file': (file_name, file_bytes, content_type)
        }
        try:
            logger.info("OCRClient: Sending extract request to %s for file %s", endpoint, file_name)
            response = requests.post(endpoint, files=files, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            logger.error("OCRClient: Request timed out for file %s: %s", file_name, e)
            raise OCRClientException("OCR service timeout.") from e
        except requests.exceptions.HTTPError as e:
            logger.error("OCRClient: HTTP error from OCR service for file %s: %s", file_name, e)
            raise OCRClientException(f"OCR service returned error status {response.status_code}.") from e
        except requests.exceptions.RequestException as e:
            logger.error("OCRClient: Request exception for file %s: %s", file_name, e)
            raise OCRClientException(f"OCR service connection failed: {e}") from e
