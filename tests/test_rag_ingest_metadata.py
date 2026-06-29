import pytest
import requests
from unittest.mock import patch
from apps.inbound.application.services.rag_service import send_to_rag


class TestRAGIngestMetadata:
    @patch("apps.inbound.application.services.rag_service.requests.post")
    def test_send_to_rag_success(self, mock_post):
        # Mock successful post
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"chunks_created": 3}

        res = send_to_rag(
            ocr_document_id="doc-12345",
            document_type="Invoice",
            warehouse_id="WH-ZONE-A",
            text="Parsed invoice document text",
            sku="SKU-TEST-99",
            product_id="prod-uuid-xyz",
            category="Tools",
            zone="Zone C",
            rack="Rack 12",
            shelf="3",
            bin="Bin 45",
        )

        assert res["success"] is True
        assert res["chunks_created"] == 3
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]

        assert payload["ocr_document_id"] == "doc-12345"
        assert payload["document_type"] == "Invoice"
        assert payload["warehouse_id"] == "WH-ZONE-A"
        assert payload["text"] == "Parsed invoice document text"
        assert payload["sku"] == "SKU-TEST-99"
        assert payload["product_id"] == "prod-uuid-xyz"
        assert payload["category"] == "Tools"
        assert payload["zone"] == "Zone C"
        assert payload["rack"] == "Rack 12"
        assert payload["shelf"] == "3"
        assert payload["bin"] == "Bin 45"

    @patch("apps.inbound.application.services.rag_service.requests.post")
    def test_send_to_rag_failure(self, mock_post):
        mock_post.side_effect = requests.RequestException("Network error")

        res = send_to_rag(
            ocr_document_id="doc-fail",
            document_type="Invoice",
            text="Failing text",
        )

        assert res["success"] is False
        assert "Network error" in res["error"]

    @patch("apps.inbound.application.services.rag_service.requests.post")
    def test_send_to_rag_default_values(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"chunks_created": 1}

        res = send_to_rag(
            ocr_document_id="doc-defaults",
            text="Minimal parameters text",
        )

        assert res["success"] is True
        assert res["chunks_created"] == 1
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]

        assert payload["ocr_document_id"] == "doc-defaults"
        assert payload["document_type"] == "OCRDocument"
        assert payload["warehouse_id"] == "WH001"
        assert payload["text"] == "Minimal parameters text"
        assert payload["sku"] is None
        assert payload["product_id"] is None
        assert payload["category"] is None
        assert payload["zone"] is None
        assert payload["rack"] is None
        assert payload["shelf"] is None
        assert payload["bin"] is None
