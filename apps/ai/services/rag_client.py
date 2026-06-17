import time
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class RAGClientException(Exception):
    """Base exception for RAGClient errors."""
    pass


class RAGTimeoutException(RAGClientException):
    """Raised when the RAG service times out."""
    pass


class RAGUnavailableException(RAGClientException):
    """Raised when the RAG service is unreachable or returns HTTP errors."""
    pass


class RAGResponseException(RAGClientException):
    """Raised when the RAG service returns an invalid or malformed response."""
    pass


class RAGClient:
    def __init__(self):
        self.base_url = getattr(settings, 'RAG_BASE_URL', 'http://localhost:8001').rstrip('/')
        self.timeout = getattr(settings, 'RAG_TIMEOUT', 30)

    def analyze(self, payload: dict, request_id: str) -> dict:
        url = f"{self.base_url}/api/ai/analyze"
        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": request_id,
        }
        
        max_retries = 3
        backoff_factor = 2  # sleep sequence: 1s, 2s, 4s

        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    "RAGClient: Sending query to %s [attempt=%d/%d] [request_id=%s]",
                    url, attempt + 1, max_retries + 1, request_id
                )
                response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()

                # Response validation
                data = response.json()
                if not isinstance(data, dict):
                    raise RAGResponseException("RAG service response is not a valid JSON object.")
                if 'suggestion' not in data:
                    raise RAGResponseException("RAG service response missing 'suggestion' field.")

                return data

            except requests.exceptions.Timeout as e:
                logger.warning(
                    "RAGClient: Timeout on attempt %d/%d for request_id %s: %s",
                    attempt + 1, max_retries + 1, request_id, str(e)
                )
                if attempt == max_retries:
                    raise RAGTimeoutException(f"RAG service timed out after {self.timeout}s.") from e

            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                logger.warning(
                    "RAGClient: Network/HTTP error on attempt %d/%d for request_id %s: %s",
                    attempt + 1, max_retries + 1, request_id, str(e)
                )
                if attempt == max_retries:
                    raise RAGUnavailableException(f"RAG service unavailable: {str(e)}.") from e

            except RAGResponseException as e:
                # Do not retry on validation error
                logger.error("RAGClient: Validation error on request_id %s: %s", request_id, str(e))
                raise

            except requests.exceptions.RequestException as e:
                logger.warning(
                    "RAGClient: Request exception on attempt %d/%d for request_id %s: %s",
                    attempt + 1, max_retries + 1, request_id, str(e)
                )
                if attempt == max_retries:
                    raise RAGUnavailableException(f"RAG service failed: {str(e)}.") from e

            # Wait with exponential backoff: 2**attempt (1s, 2s, 4s)
            sleep_time = backoff_factor ** attempt
            logger.info("RAGClient: Sleeping for %d seconds before retry...", sleep_time)
            time.sleep(sleep_time)

        raise RAGUnavailableException("RAG service failed after maximum retries.")

    def ping(self) -> bool:
        url = f"{self.base_url}/status"
        try:
            logger.info("RAGClient: Pinging RAG service status endpoint: %s", url)
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error("RAGClient: Health check ping failed: %s", e)
            return False
