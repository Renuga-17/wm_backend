import pytest
import requests
import json
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from apps.identity.infrastructure.persistence.models import User
from apps.inbound.infrastructure.persistence.models import OCRDocument


@pytest.mark.django_db
class TestRAGQueryAPI:
    @pytest.fixture(autouse=True)
    def setup_user(self):
        self.username = "testraguser"
        self.password = "testragpassword"
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email="testrag@example.com",
            full_name="Test RAG User",
        )
        # Setup standard API client authentication headers
        self.login_url = reverse("token_obtain_pair")

    def get_auth_headers(self, client):
        res = client.post(
            self.login_url,
            {"username": self.username, "password": self.password},
            content_type="application/json"
        )
        assert res.status_code == status.HTTP_200_OK
        access_token = res.data["access"]
        return {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}

    @patch("apps.ai.services.rag_client.requests.post")
    def test_query_success(self, mock_post, client):
        headers = self.get_auth_headers(client)

        # Mock RAG response
        mock_response = patch("requests.Response").start()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "suggestion": json.dumps({
                "analysis_summary": "Located item at Zone A Rack 2.",
                "possible_issues": [],
                "recommended_actions": ["Proceed to Zone A."],
                "document_reference": ["Invoice section 3"],
                "confidence": 0.95
            }),
            "confidence": 0.95,
            "predictedCategory": "Invoices",
            "status": "SUCCESS"
        }
        mock_post.return_value = mock_response

        # Setup an OCR document in DB for source parsing
        doc = OCRDocument.objects.create(
            file_name="invoice_123.pdf",
            file_path="/media/invoice_123.pdf",
            document_type="invoice",
            raw_text="SKU_ABC_123 found in invoice",
            processing_status=OCRDocument.ProcessingStatus.COMPLETED
        )

        query_url = "/api/ai/query/"
        payload = {
            "query": "Where is product SKU_ABC_123?",
            "sku": "SKU_ABC_123",
            "document_type": "invoice"
        }

        res = client.post(
            query_url,
            payload,
            content_type="application/json",
            **headers
        )

        assert res.status_code == status.HTTP_200_OK
        assert "request_id" in res.data
        assert res.data["answer"] == "Located item at Zone A Rack 2."
        assert len(res.data["sources"]) > 0
        assert res.data["sources"][0]["document_id"] == str(doc.id)
        assert res.data["sources"][0]["document_type"] == "invoice"
        assert res.data["sources"][0]["sku"] == "SKU_ABC_123"
        assert res.data["filters"]["sku"] == "SKU_ABC_123"
        assert res.data["filters"]["document_type"] == "invoice"

    @patch("apps.ai.services.rag_client.requests.post")
    def test_query_metadata_filters(self, mock_post, client):
        headers = self.get_auth_headers(client)

        mock_response = patch("requests.Response").start()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "suggestion": "Generic info",
            "confidence": 0.8,
            "predictedCategory": "General",
            "status": "SUCCESS"
        }
        mock_post.return_value = mock_response

        query_url = "/api/ai/query/"
        payload = {
            "query": "Find the general shelf rule.",
            "sku": "SKU_XYZ",
            "product_id": "PROD_XYZ",
            "category": "dry_goods",
            "warehouse_id": "WH001",
            "zone": "Zone B",
            "rack": "Rack 1",
            "shelf": "Shelf 3",
            "bin": "Bin 5",
            "document_type": "manual"
        }

        res = client.post(
            query_url,
            payload,
            content_type="application/json",
            **headers
        )

        assert res.status_code == status.HTTP_200_OK
        # Verify the post parameters sent to the client (mock_post.call_args)
        args, kwargs = mock_post.call_args
        sent_payload = kwargs["json"]
        assert sent_payload["sku"] == "SKU_XYZ"
        assert sent_payload["productId"] == "PROD_XYZ"
        assert sent_payload["category"] == "dry_goods"
        assert sent_payload["warehouseId"] == "WH001"
        assert sent_payload["zone"] == "Zone B"
        assert sent_payload["rack"] == "Rack 1"
        assert sent_payload["bin"] == "Bin 5"
        assert sent_payload["documentType"] == "manual"
        assert sent_payload["userId"] is not None  # checks User UUID -> int conversion

    def test_authentication_failure(self, client):
        query_url = "/api/ai/query/"
        res = client.post(
            query_url,
            {"query": "Should fail"},
            content_type="application/json"
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("apps.ai.services.rag_client.requests.post")
    def test_timeout_handling(self, mock_post, client):
        headers = self.get_auth_headers(client)

        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        query_url = "/api/ai/query/"
        res = client.post(
            query_url,
            {"query": "Timeout test"},
            content_type="application/json",
            **headers
        )
        assert res.status_code == status.HTTP_504_GATEWAY_TIMEOUT
        assert "error" in res.data
        assert "timed out" in res.data["error"]

    @patch("apps.ai.services.rag_client.requests.post")
    def test_service_unavailable(self, mock_post, client):
        headers = self.get_auth_headers(client)

        mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        query_url = "/api/ai/query/"
        res = client.post(
            query_url,
            {"query": "Connection test"},
            content_type="application/json",
            **headers
        )
        assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "error" in res.data
        assert "unavailable" in res.data["error"]

    @patch("apps.ai.services.rag_client.requests.post")
    def test_invalid_response_handling(self, mock_post, client):
        headers = self.get_auth_headers(client)

        # Mock an invalid json response (missing 'suggestion')
        mock_response = patch("requests.Response").start()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "invalid_field": "some data"
        }
        mock_post.return_value = mock_response

        query_url = "/api/ai/query/"
        res = client.post(
            query_url,
            {"query": "Invalid json structure test"},
            content_type="application/json",
            **headers
        )
        assert res.status_code == status.HTTP_502_BAD_GATEWAY
        assert "error" in res.data
        assert "invalid response" in res.data["error"]

    @patch("apps.ai.services.rag_client.requests.get")
    def test_health_endpoint_success(self, mock_get, client):
        mock_response = patch("requests.Response").start()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        health_url = "/api/ai/rag-health/"
        res = client.get(health_url)

        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "healthy"

    @patch("apps.ai.services.rag_client.requests.get")
    def test_health_endpoint_failure(self, mock_get, client):
        mock_get.side_effect = Exception("Service offline")

        health_url = "/api/ai/rag-health/"
        res = client.get(health_url)

        assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert res.data["status"] == "unavailable"
