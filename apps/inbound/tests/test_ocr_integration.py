import uuid
import hashlib
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.inbound.infrastructure.persistence.models import OCRDocument, InboundShipment
from apps.inventory.infrastructure.persistence.models import Product, ProductDimension
from apps.recommendations.models.storage_recommendation import StorageRecommendation
from apps.recommendations.models.bin_allocation import BinAllocation
from apps.recommendations.models.bin_3d_placement import Bin3DPlacement
from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin, NavigationNode
from apps.inbound.services.ocr_client import OCRClientException

User = get_user_model()


class OCRIntegrationTestCase(TestCase):
    def setUp(self):
        # Clear tables to ensure absolute isolation between tests
        OCRDocument.objects.all().delete()
        InboundShipment.objects.all().delete()
        Product.objects.all().delete()

        self.client = APIClient()
        self.user = User.objects.create_user(
            username='ocr_test_user',
            password='testpassword123',
            email='ocr_test@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        # Build warehouse spatial graph structure so downstream WMS engines succeed
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

        # Setup standard docking node for navigation router
        self.nav_node = NavigationNode.objects.create(
            warehouse=self.warehouse,
            node_name='Receiving-Dock-1',
            node_type='DOCK',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0')
        )

        # Standard successful response payload from mock OCR Microservice
        self.mock_success_payload = {
            'status': 'success',
            'file_name': 'invoice_test.png',
            'document_type': 'invoice',
            'confidence_score': 0.96,
            'raw_text': 'INVOICE NUM: INV-2026-001\nSUPPLIER: LOGITECH\nDELIVERY: 2026-06-12\nITEM: SKU-MOUSE-01\nSIZE: 15.0x10.0x5.0\nWEIGHT: 0.25',
            'extracted_data': {
                'document_info': {
                    'invoice_number': 'INV-2026-001',
                    'delivery_number': 'DEL-2026-001'
                },
                'party_info': {
                    'supplier_name': 'LOGITECH'
                },
                'shipment_info': {
                    'delivery_date': '2026-06-12T10:00:00Z'
                },
                'products': [
                    {
                        'sku': 'SKU-MOUSE-01',
                        'product_name': 'Logitech MX Master Mouse',
                        'category': 'Electronics',
                        'quantity': 50,
                        'weight': {'value': 0.25, 'unit': 'kg'},
                        'dimensions': {'length': 15.0, 'width': 10.0, 'height': 5.0, 'unit': 'cm'},
                        'is_fragile': False,
                        'is_hazardous': False
                    }
                ]
            }
        }

    @patch('apps.inbound.services.ocr_client.requests.post')
    def test_upload_success_and_downstream_pipeline(self, mock_post):
        """Test file upload triggers OCR client, saves document, and processes downstream WMS pipeline."""
        # 1. Mock requests.post to return the successful payload
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = self.mock_success_payload

        # 2. Perform upload
        file_content = b"fake invoice image binary data"
        test_file = SimpleUploadedFile("invoice_test.png", file_content, content_type="image/png")

        upload_url = '/api/ocr/upload/'
        response = self.client.post(upload_url, {'file': test_file, 'document_type': 'invoice'}, format='multipart')

        # 3. Verify response status and body
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('document_id', response.data)
        doc_id = response.data['document_id']
        self.assertEqual(response.data['status'], 'COMPLETED')  # COMPLETED because tests run synchronously

        # 4. Verify OCRDocument is stored properly in DB
        doc = OCRDocument.objects.get(id=doc_id)
        self.assertEqual(doc.processing_status, OCRDocument.ProcessingStatus.COMPLETED)
        self.assertEqual(doc.file_name, 'invoice_test.png')
        self.assertEqual(doc.confidence_score, 0.96)
        self.assertEqual(doc.raw_text, self.mock_success_payload['raw_text'])

        # Calculate file hash to verify correct hash mapping
        expected_hash = hashlib.sha256(file_content).hexdigest()
        self.assertEqual(doc.document_hash, expected_hash)

        # 5. Verify downstream WMS ingestion pipeline entities were created
        # Check InboundShipment
        self.assertTrue(InboundShipment.objects.filter(shipment_code='INV-2026-001').exists())
        shipment = InboundShipment.objects.get(shipment_code='INV-2026-001')
        self.assertEqual(shipment.supplier_name, 'LOGITECH')
        self.assertEqual(shipment.status, 'RECEIVED')

        # Check Product
        self.assertTrue(Product.objects.filter(sku='SKU-MOUSE-01').exists())
        product = Product.objects.get(sku='SKU-MOUSE-01')
        self.assertEqual(product.product_name, 'Logitech MX Master Mouse')
        self.assertEqual(product.weight, Decimal('0.25'))

        # Check ProductDimension
        self.assertTrue(ProductDimension.objects.filter(product=product).exists())
        dim = ProductDimension.objects.get(product=product)
        self.assertEqual(dim.length, Decimal('15.00'))
        self.assertEqual(dim.width, Decimal('10.00'))
        self.assertEqual(dim.height, Decimal('5.00'))

        # Check StorageRecommendation
        self.assertTrue(StorageRecommendation.objects.filter(product=product).exists())
        rec = StorageRecommendation.objects.get(product=product)
        self.assertEqual(rec.zone, self.zone)
        self.assertEqual(rec.zone_group, self.zone_group)

        # Check BinAllocation
        self.assertTrue(BinAllocation.objects.filter(product=product).exists())
        alloc = BinAllocation.objects.get(product=product)
        self.assertEqual(alloc.bin, self.bin)

        # Check 3D Placement
        self.assertTrue(Bin3DPlacement.objects.filter(bin_allocation=alloc).exists())
        placement = Bin3DPlacement.objects.get(bin_allocation=alloc)
        self.assertEqual(placement.position_x, Decimal('0.00'))
        self.assertEqual(placement.position_y, Decimal('0.00'))
        self.assertEqual(placement.position_z, Decimal('0.00'))

    @patch('apps.inbound.services.ocr_client.requests.post')
    def test_duplicate_upload_detection(self, mock_post):
        """Test that uploading the same file twice returns 200 OK with the same ID and doesn't run OCR twice."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = self.mock_success_payload

        file_content = b"unique file contents for duplication check"
        test_file_1 = SimpleUploadedFile("invoice_dup.png", file_content, content_type="image/png")
        test_file_2 = SimpleUploadedFile("invoice_dup.png", file_content, content_type="image/png")

        upload_url = '/api/ocr/upload/'

        # Upload 1
        response_1 = self.client.post(upload_url, {'file': test_file_1}, format='multipart')
        self.assertEqual(response_1.status_code, status.HTTP_201_CREATED)
        doc_id_1 = response_1.data['document_id']

        # Reset mock call count to verify it is not called during duplicate upload
        mock_post.reset_mock()

        # Upload 2 (identical content)
        response_2 = self.client.post(upload_url, {'file': test_file_2}, format='multipart')

        # Should return 200 OK with the existing document_id
        self.assertEqual(response_2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_2.data['document_id'], doc_id_1)
        self.assertEqual(response_2.data['status'], 'COMPLETED')

        # OCR request should NOT have been sent a second time
        mock_post.assert_not_called()

    @patch('apps.inbound.services.ocr_client.requests.post')
    def test_ocr_microservice_failure_mapping(self, mock_post):
        """Test that a failure in the OCR client fails the task gracefully and populates error details."""
        # Mock connection failure
        mock_post.side_effect = Exception("Connection refused by OCR server")

        file_content = b"fail file bytes"
        test_file = SimpleUploadedFile("invoice_fail.png", file_content, content_type="image/png")

        upload_url = '/api/ocr/upload/'
        response = self.client.post(upload_url, {'file': test_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc_id = response.data['document_id']
        self.assertEqual(response.data['status'], 'FAILED')

        # Check document in DB
        doc = OCRDocument.objects.get(id=doc_id)
        self.assertEqual(doc.processing_status, OCRDocument.ProcessingStatus.FAILED)
        self.assertIn("Connection refused", doc.error_message)

    @patch('apps.inbound.services.ocr_client.requests.post')
    def test_review_queue_path_trigger(self, mock_post):
        """Test that confidence score < 0.85 sets status to REVIEW_REQUIRED and blocks downstream pipeline."""
        mock_low_confidence = self.mock_success_payload.copy()
        mock_low_confidence['confidence_score'] = 0.80  # Below 0.85
        mock_low_confidence['extracted_data'] = self.mock_success_payload['extracted_data'].copy()
        mock_low_confidence['extracted_data']['products'] = [
            {
                'sku': 'SKU-LOW-CONF',
                'product_name': 'Low Confidence Product',
                'category': 'Electronics',
                'quantity': 10,
                'weight': 1.0,
                'dimensions': {'length': 10.0, 'width': 10.0, 'height': 10.0},
                'is_fragile': False,
                'is_hazardous': False
            }
        ]

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_low_confidence

        file_content = b"low confidence file data"
        test_file = SimpleUploadedFile("invoice_low_conf.png", file_content, content_type="image/png")

        upload_url = '/api/ocr/upload/'
        response = self.client.post(upload_url, {'file': test_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc_id = response.data['document_id']
        self.assertEqual(response.data['status'], 'REVIEW_REQUIRED')

        # Check DB status
        doc = OCRDocument.objects.get(id=doc_id)
        self.assertEqual(doc.processing_status, OCRDocument.ProcessingStatus.REVIEW_REQUIRED)
        self.assertEqual(doc.confidence_score, 0.80)

        # Check that downstream objects were NOT created
        # No product should be created
        self.assertFalse(Product.objects.filter(sku='SKU-LOW-CONF').exists())
        # No InboundShipment should be created
        self.assertFalse(InboundShipment.objects.filter(shipment_code='INV-2026-001').exists())

    def test_status_check_endpoint(self):
        """Test retrieval of specific OCR document status and info."""
        doc = OCRDocument.objects.create(
            file_name='status_test.pdf',
            file_path='ocr_documents/status_test.pdf',
            document_type='invoice',
            document_hash='hash12345',
            confidence_score=0.92,
            processing_status=OCRDocument.ProcessingStatus.COMPLETED
        )

        url = f'/api/ocr/documents/{doc.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document_id'], str(doc.id))
        self.assertEqual(response.data['status'], 'COMPLETED')
        self.assertEqual(response.data['document_type'], 'invoice')
        self.assertEqual(response.data['confidence_score'], 0.92)

    def test_history_audit_endpoint_with_filters(self):
        """Test log/history view with filtering capabilities."""
        # Create documents with various statuses and types
        doc_1 = OCRDocument.objects.create(
            file_name='doc_1.png',
            file_path='ocr_documents/doc_1.png',
            document_type='invoice',
            confidence_score=0.95,
            processing_status=OCRDocument.ProcessingStatus.COMPLETED
        )
        doc_2 = OCRDocument.objects.create(
            file_name='doc_2.pdf',
            file_path='ocr_documents/doc_2.pdf',
            document_type='po',
            confidence_score=0.91,
            processing_status=OCRDocument.ProcessingStatus.COMPLETED
        )
        doc_3 = OCRDocument.objects.create(
            file_name='doc_3.png',
            file_path='ocr_documents/doc_3.png',
            document_type='invoice',
            confidence_score=0.78,
            processing_status=OCRDocument.ProcessingStatus.REVIEW_REQUIRED
        )

        history_url = '/api/ocr/documents/'

        # Get all history
        res_all = self.client.get(history_url)
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        data_results = res_all.data['results'] if isinstance(res_all.data, dict) and 'results' in res_all.data else res_all.data
        self.assertEqual(len(data_results), 3)

        # Filter by status: REVIEW_REQUIRED
        res_status = self.client.get(f'{history_url}?status=REVIEW_REQUIRED')
        self.assertEqual(res_status.status_code, status.HTTP_200_OK)
        status_results = res_status.data['results'] if isinstance(res_status.data, dict) and 'results' in res_status.data else res_status.data
        self.assertEqual(len(status_results), 1)
        self.assertEqual(status_results[0]['file_name'], 'doc_3.png')

        # Filter by document_type: po
        res_type = self.client.get(f'{history_url}?document_type=po')
        self.assertEqual(res_type.status_code, status.HTTP_200_OK)
        type_results = res_type.data['results'] if isinstance(res_type.data, dict) and 'results' in res_type.data else res_type.data
        self.assertEqual(len(type_results), 1)
        self.assertEqual(type_results[0]['file_name'], 'doc_2.pdf')
