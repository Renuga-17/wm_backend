import uuid
import hashlib
from decimal import Decimal
from typing import Any
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.inbound.infrastructure.persistence.models import OCRDocument, InboundShipment
from apps.inventory.infrastructure.persistence.models import Product, ProductDimension
from apps.recommendations.models.storage_recommendation import StorageRecommendation
from apps.recommendations.models.bin_allocation import BinAllocation
from apps.recommendations.models.bin_3d_placement import Bin3DPlacement
from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin, NavigationNode

User = get_user_model()


class OCRReviewQueueTestCase(TestCase):
    def setUp(self):
        OCRDocument.objects.all().delete()
        InboundShipment.objects.all().delete()
        Product.objects.all().delete()

        self.client = APIClient()
        self.user = User.objects.create_user(  # type: ignore
            username='review_test_user',
            password='testpassword123',
            email='review_test@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        # Build warehouse spatial structure so downstream WMS engines succeed
        self.warehouse = Warehouse.objects.create(
            name='Test Inbound Warehouse',
            location='Dock Area 1',
            total_area_sqft=Decimal('2500.00')
        )
        self.zone_group = ZoneGroup.objects.create(
            warehouse=self.warehouse,
            code='G1',
            name='General Storage Group',
            zone_group_type='GENERAL_STORAGE'
        )
        self.zone = Zone.objects.create(
            warehouse=self.warehouse,
            zone_group=self.zone_group,
            zone_name='Zone-G1',
            zone_type='GENERAL',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0'),
            width=Decimal('20.0'), height=Decimal('20.0'), depth=Decimal('20.0')
        )
        self.rack = Rack.objects.create(
            zone=self.zone,
            rack_code='RACK-G1-1',
            max_weight=Decimal('1000.00'),
            x=Decimal('2.0'), y=Decimal('2.0'), z=Decimal('0.0'),
            width=Decimal('3.0'), height=Decimal('10.0'), depth=Decimal('1.5'),
            rotation_angle=Decimal('0.0')
        )
        self.shelf = Shelf.objects.create(
            rack=self.rack,
            shelf_number=1,
            max_weight=Decimal('500.00'),
            height_from_ground=Decimal('0.0')
        )
        self.bin = Bin.objects.create(
            shelf=self.shelf,
            bin_code='BIN-G1-1-01',
            max_capacity=Decimal('50.00'),
            current_capacity=Decimal('0.00'),
            length=Decimal('100.00'),
            width=Decimal('100.00'),
            height=Decimal('100.00'),
            is_occupied=False
        )
        self.nav_node = NavigationNode.objects.create(
            warehouse=self.warehouse,
            node_name='Receiving-Dock-1',
            node_type='DOCK',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0')
        )

        self.extracted_json_payload = {
            'status': 'success',
            'file_name': 'invoice_review.png',
            'document_type': 'invoice',
            'confidence_score': 0.78,
            'raw_text': 'INVOICE NUM: INV-2026-999\nSUPPLIER: ACME\nDELIVERY: 2026-06-12\nITEM: SKU-KEYBOARD-01\nSIZE: 30.0x15.0x4.0\nWEIGHT: 0.85',
            'extracted_data': {
                'document_info': {
                    'invoice_number': 'INV-2026-999',
                    'delivery_number': 'DEL-2026-999'
                },
                'party_info': {
                    'supplier_name': 'ACME'
                },
                'shipment_info': {
                    'delivery_date': '2026-06-12T10:00:00Z'
                },
                'products': [
                    {
                        'sku': 'SKU-KEYBOARD-01',
                        'product_name': 'Acme Mechanical Keyboard',
                        'category': 'Electronics',
                        'quantity': 20,
                        'weight': {'value': 0.85, 'unit': 'kg'},
                        'dimensions': {'length': 30.0, 'width': 15.0, 'height': 4.0, 'unit': 'cm'},
                        'is_fragile': False,
                        'is_hazardous': False
                    }
                ]
            }
        }

    def test_review_queue_endpoint(self):
        """Test that only documents in REVIEW_REQUIRED status are returned by the review-queue."""
        # Create different documents
        doc_review = OCRDocument.objects.create(
            file_name='review.png',
            file_path='ocr_documents/review.png',
            document_type='invoice',
            processing_status=OCRDocument.ProcessingStatus.REVIEW_REQUIRED,
            confidence_score=0.75
        )
        doc_completed = OCRDocument.objects.create(
            file_name='completed.png',
            file_path='ocr_documents/completed.png',
            document_type='invoice',
            processing_status=OCRDocument.ProcessingStatus.COMPLETED,
            confidence_score=0.95
        )

        response: Any = self.client.get('/api/ocr/review-queue/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(doc_review.id))
        self.assertEqual(results[0]['processing_status'], 'REVIEW_REQUIRED')

    def test_ocr_detail_endpoint(self):
        """Test that OCR detail endpoint returns the necessary fields for review."""
        doc = OCRDocument.objects.create(
            file_name='detail_test.png',
            file_path='ocr_documents/detail_test.png',
            document_type='invoice',
            raw_text='Raw text contents here...',
            extracted_json={'extracted_data': {'supplier': 'ACME'}},
            confidence_score=0.72,
            processing_status=OCRDocument.ProcessingStatus.REVIEW_REQUIRED
        )

        url = f'/api/ocr/documents/{doc.id}/'
        response: Any = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['raw_text'], 'Raw text contents here...')
        self.assertEqual(response.data['extracted_json'], {'extracted_data': {'supplier': 'ACME'}})
        self.assertEqual(response.data['confidence_score'], 0.72)
        self.assertEqual(response.data['processing_status'], 'REVIEW_REQUIRED')
        self.assertEqual(response.data['document_type'], 'invoice')

    @patch('requests.post')
    def test_ocr_approve_endpoint_without_corrections(self, mock_post):
        """Test approving a document without any corrections resumes and finishes the WMS pipeline."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "SUCCESS"}

        doc = OCRDocument.objects.create(
            file_name='invoice_review.png',
            file_path='ocr_documents/invoice_review.png',
            document_type='invoice',
            document_hash='hash99999',
            extracted_json=self.extracted_json_payload,
            confidence_score=0.78,
            processing_status=OCRDocument.ProcessingStatus.REVIEW_REQUIRED
        )

        url = f'/api/ocr/documents/{doc.id}/approve/'
        response: Any = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify OCRDocument state changes: REVIEW_REQUIRED -> APPROVED -> COMPLETED
        doc.refresh_from_db()
        self.assertEqual(doc.processing_status, OCRDocument.ProcessingStatus.COMPLETED)

        # Verify downstream WMS ingestion occurred
        self.assertTrue(InboundShipment.objects.filter(shipment_code='INV-2026-999').exists())
        self.assertTrue(Product.objects.filter(sku='SKU-KEYBOARD-01').exists())
        self.assertTrue(StorageRecommendation.objects.filter(product__sku='SKU-KEYBOARD-01').exists())
        self.assertTrue(BinAllocation.objects.filter(product__sku='SKU-KEYBOARD-01').exists())
        self.assertTrue(Bin3DPlacement.objects.filter(bin_allocation__product__sku='SKU-KEYBOARD-01').exists())

        # Verify RAG trigger was fired
        mock_post.assert_called()
        rag_call_args = mock_post.call_args_list[0]
        self.assertIn("api/rag/ingest", rag_call_args[0][0])

    @patch('requests.post')
    def test_ocr_approve_endpoint_with_corrections(self, mock_post):
        """Test approving a document with payload corrections resolves custom values."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "SUCCESS"}

        doc = OCRDocument.objects.create(
            file_name='invoice_review.png',
            file_path='ocr_documents/invoice_review.png',
            document_type='invoice',
            document_hash='hash88888',
            extracted_json=self.extracted_json_payload,
            confidence_score=0.78,
            processing_status=OCRDocument.ProcessingStatus.REVIEW_REQUIRED
        )

        # Correct supplier name and product quantity/name in payload
        corrected_payload: dict[str, Any] = self.extracted_json_payload.copy()
        corrected_payload['extracted_data'] = self.extracted_json_payload['extracted_data'].copy()
        corrected_payload['extracted_data']['party_info'] = {'supplier_name': 'ACME INTERNATIONAL'}
        corrected_payload['extracted_data']['products'] = [
            {
                'sku': 'SKU-KEYBOARD-01',
                'product_name': 'Corrected Mechanical Keyboard',
                'category': 'Electronics',
                'quantity': 35,
                'weight': {'value': 0.85, 'unit': 'kg'},
                'dimensions': {'length': 30.0, 'width': 15.0, 'height': 4.0}
            }
        ]

        url = f'/api/ocr/documents/{doc.id}/approve/'
        response: Any = self.client.post(url, {'extracted_json': corrected_payload}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        doc.refresh_from_db()
        self.assertEqual(doc.processing_status, OCRDocument.ProcessingStatus.COMPLETED)
        self.assertIsNotNone(doc.extracted_json)
        assert doc.extracted_json is not None
        self.assertEqual(doc.extracted_json['extracted_data']['party_info']['supplier_name'], 'ACME INTERNATIONAL')

        # Check corrected ingestion values in WMS models
        shipment = InboundShipment.objects.get(shipment_code='INV-2026-999')
        self.assertEqual(shipment.supplier_name, 'ACME INTERNATIONAL')

        product = Product.objects.get(sku='SKU-KEYBOARD-01')
        self.assertEqual(product.product_name, 'Corrected Mechanical Keyboard')

    def test_ocr_reject_endpoint(self):
        """Test that POST reject marks document as REJECTED and stores rejection reason."""
        doc = OCRDocument.objects.create(
            file_name='invoice_review.png',
            file_path='ocr_documents/invoice_review.png',
            document_type='invoice',
            extracted_json=self.extracted_json_payload,
            confidence_score=0.78,
            processing_status=OCRDocument.ProcessingStatus.REVIEW_REQUIRED
        )

        url = f'/api/ocr/documents/{doc.id}/reject/'
        response: Any = self.client.post(url, {'reason': 'Incorrect supplier document'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['processing_status'], 'REJECTED')

        doc.refresh_from_db()
        self.assertEqual(doc.processing_status, OCRDocument.ProcessingStatus.REJECTED)
        self.assertEqual(doc.rejection_reason, 'Incorrect supplier document')

        # Assert no downstream WMS data exists
        self.assertFalse(InboundShipment.objects.filter(shipment_code='INV-2026-999').exists())
        self.assertFalse(Product.objects.filter(sku='SKU-KEYBOARD-01').exists())

    def test_ocr_approve_invalid_status_raises_error(self):
        """Test trying to approve a completed document raises a validation error."""
        doc = OCRDocument.objects.create(
            file_name='completed_test.png',
            file_path='ocr_documents/completed_test.png',
            document_type='invoice',
            processing_status=OCRDocument.ProcessingStatus.COMPLETED
        )

        url = f'/api/ocr/documents/{doc.id}/approve/'
        response: Any = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot approve document in status", response.data['error'])
