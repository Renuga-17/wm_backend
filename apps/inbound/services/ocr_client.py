import os
import requests
import logging

logger = logging.getLogger(__name__)


class OCRClientException(Exception):
    pass


class OCRClient:
    def __init__(self):
        # OCR_SERVICE_URL must be set to the ngrok URL when OCR runs on a remote machine.
        # Example: OCR_SERVICE_URL=https://xxxx-xx-xxx-xxx-xxx.ngrok-free.app
        # Do NOT use localhost:8001 unless the OCR service is running on this machine.
        ocr_url = os.getenv('OCR_SERVICE_URL', '')
        if not ocr_url:
            logger.warning(
                "[OCR Client] OCR_SERVICE_URL is not set. "
                "Requests will fail. Set it to your ngrok URL in the .env file."
            )
        self.url = ocr_url.rstrip('/')
        try:
            self.timeout = int(os.getenv('OCR_TIMEOUT', '60'))
        except ValueError:
            self.timeout = 60

    def extract_document(self, file_bytes: bytes, file_name: str, content_type: str = 'application/octet-stream') -> dict:
        endpoint = f"{self.url}/api/v1/ocr/extract"
        logger.info("[OCR PIPELINE] Using OCR Service URL: %s", self.url)
        logger.info("[OCR PIPELINE] OCR request started for file: %s (endpoint: %s)", file_name, endpoint)

        files = {
            'file': (file_name, file_bytes, content_type)
        }
        headers = {
            'ngrok-skip-browser-warning': 'true'
        }
        try:
            response = requests.post(endpoint, files=files, headers=headers, timeout=self.timeout)
            logger.info("[OCR PIPELINE] OCR response received with status code: %d", response.status_code)
            response.raise_for_status()
            
            result = response.json()
            logger.info("[OCR PIPELINE] OCR extraction succeeded and response JSON parsed.")
            return result
        except requests.exceptions.Timeout as e:
            logger.error("[OCR PIPELINE] Request timed out for file %s: %s", file_name, e)
            raise OCRClientException("OCR service timeout.") from e
        except requests.exceptions.HTTPError as e:
            logger.error("[OCR PIPELINE] HTTP error from OCR service for file %s: %s", file_name, e)
            raise OCRClientException(f"OCR service returned error status {response.status_code}.") from e
        except requests.exceptions.RequestException as e:
            logger.error("[OCR PIPELINE] Request exception for file %s: %s", file_name, e)
            raise OCRClientException(f"OCR service connection failed: {e}") from e
