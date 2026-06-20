import uuid
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.inbound.infrastructure.persistence.models import OCRDocument, InboundShipment
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, ProductDimension
from apps.recommendations.models.bin_allocation import BinAllocation
from apps.recommendations.models.storage_recommendation import StorageRecommendation
from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin

User = get_user_model()


class RAGSyncTestCase(TestCase):
    def setUp(self):
        OCRDocument.objects.all().delete()
        InboundShipment.objects.all().delete()
        Product.objects.all().delete()

        self.client = APIClient()
        self.user = User.objects.create_user(
            username='rag_test_user',
            password='testpassword123',
            email='rag_test@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        # Build warehouse structure
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

        self.extracted_json_payload = {
            'extracted_data': {
                'document_info': {
                    'invoice_number': 'INV-TEST-999',
                },
                'party_info': {
                    'supplier_name': 'TEST-SUPPLIER'
                },
                'products': [
                    {
                        'sku': 'SKU-RAG-01',
                        'product_name': 'RAG Sync Test Product',
                        'category': 'Electronics',
                        'quantity': 5,
                        'weight': 1.2,
                        'dimensions': {'length': 5.0, 'width': 5.0, 'height': 5.0},
                        'is_fragile': False,
                        'is_hazardous': False
                    }
                ]
            }
        }

    @patch('apps.inbound.application.services.rag_service.requests.post')
    def test_sync_document_to_rag_extracts_correct_metadata(self, mock_post):
        """Test that sync_document_to_rag correctly extracts product and allocation metadata and calls send_to_rag."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Create OCRDocument, Product, BinAllocation in completed state
        ocr_doc = OCRDocument.objects.create(
            file_name='test.pdf',
            file_path='ocr_documents/test.pdf',
            document_type='invoice',
            raw_text='SKU-RAG-01 is a test product.',
            extracted_json=self.extracted_json_payload,
            processing_status=OCRDocument.ProcessingStatus.COMPLETED
        )

        category = ProductCategory.objects.create(category_name='Electronics')
        product = Product.objects.create(
            sku='SKU-RAG-01',
            product_name='RAG Sync Test Product',
            category=category,
            weight=1.2
        )

        allocation = BinAllocation.objects.create(
            product=product,
            zone_group=self.zone_group,
            zone=self.zone,
            rack=self.rack,
            shelf=self.shelf,
            bin=self.bin,
            allocation_score=0.9,
            allocation_reason='Test logic',
            selected_orientation='0'
        )

        from apps.inbound.application.services.rag_service import sync_document_to_rag
        success = sync_document_to_rag(ocr_doc)

        self.assertTrue(success)
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs['json']

        self.assertEqual(payload['ocr_document_id'], str(ocr_doc.id))
        self.assertEqual(payload['sku'], 'SKU-RAG-01')
        self.assertEqual(payload['product_id'], str(product.id))
        self.assertEqual(payload['category'], 'Electronics')
        self.assertEqual(payload['warehouse_id'], str(self.warehouse.id))
        self.assertEqual(payload['zone'], self.zone.zone_name)
        self.assertEqual(payload['rack'], self.rack.rack_code)
        self.assertEqual(payload['shelf'], str(self.shelf.shelf_number))
        self.assertEqual(payload['bin'], self.bin.bin_code)

    @patch('apps.inbound.application.services.rag_service.requests.post')
    def test_sync_rag_endpoint_success(self, mock_post):
        """Test the POST /api/ocr/documents/{id}/sync-rag/ custom action view endpoint on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        ocr_doc = OCRDocument.objects.create(
            file_name='test.pdf',
            file_path='ocr_documents/test.pdf',
            document_type='invoice',
            raw_text='Invoice test data',
            processing_status=OCRDocument.ProcessingStatus.COMPLETED
        )

        url = f'/api/ocr/documents/{ocr_doc.id}/sync-rag/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['message'], "OCR Document successfully synced to RAG.")

    @patch('apps.inbound.application.services.rag_service.requests.post')
    def test_sync_rag_endpoint_bad_status(self, mock_post):
        """Test that POST /api/ocr/documents/{id}/sync-rag/ rejects if document is not completed."""
        ocr_doc = OCRDocument.objects.create(
            file_name='test.pdf',
            file_path='ocr_documents/test.pdf',
            document_type='invoice',
            raw_text='Invoice test data',
            processing_status=OCRDocument.ProcessingStatus.REVIEW_REQUIRED
        )

        url = f'/api/ocr/documents/{ocr_doc.id}/sync-rag/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("must be COMPLETED", response.data['error'])
        mock_post.assert_not_called()

    @patch('apps.inbound.application.services.rag_service.requests.post')
    def test_sync_rag_endpoint_failure(self, mock_post):
        """Test the POST /api/ocr/documents/{id}/sync-rag/ custom action view endpoint when RAG service is down."""
        mock_post.side_effect = Exception("RAG service unavailable")

        ocr_doc = OCRDocument.objects.create(
            file_name='test.pdf',
            file_path='ocr_documents/test.pdf',
            document_type='invoice',
            raw_text='Invoice test data',
            processing_status=OCRDocument.ProcessingStatus.COMPLETED
        )

        url = f'/api/ocr/documents/{ocr_doc.id}/sync-rag/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Failed to sync document", response.data['error'])

    @patch('apps.inbound.tasks.sync_rag_task.delay')
    def test_inbound_orchestrator_triggers_async_task(self, mock_delay):
        """Test that InboundOrchestratorService queues the sync_rag_task Celery task asynchronously."""
        ocr_doc = OCRDocument.objects.create(
            file_name='test.pdf',
            file_path='ocr_documents/test.pdf',
            document_type='invoice',
            raw_text='Invoice test data',
            extracted_json=self.extracted_json_payload,
            processing_status=OCRDocument.ProcessingStatus.APPROVED
        )

        from apps.inbound.application.services.inbound_orchestrator_service import InboundOrchestratorService
        orchestrator = InboundOrchestratorService()
        shipment = orchestrator.orchestrate_inbound(ocr_doc)

        self.assertIsNotNone(shipment)
        self.assertEqual(ocr_doc.processing_status, OCRDocument.ProcessingStatus.COMPLETED)
        mock_delay.assert_called_once_with(str(ocr_doc.id))

    @patch('apps.inbound.application.services.rag_service.requests.post')
    def test_rag_sync_failure_does_not_rollback_ingest(self, mock_post):
        """Test that if RAG ingestion fails, the database products/shipments are NOT rolled back, and the document is COMPLETED."""
        mock_post.side_effect = Exception("RAG server connection refused")

        ocr_doc = OCRDocument.objects.create(
            file_name='test.pdf',
            file_path='ocr_documents/test.pdf',
            document_type='invoice',
            raw_text='Invoice test data',
            extracted_json=self.extracted_json_payload,
            processing_status=OCRDocument.ProcessingStatus.APPROVED
        )

        from apps.inbound.application.services.inbound_orchestrator_service import InboundOrchestratorService
        orchestrator = InboundOrchestratorService()
        
        # RAG sync failure should still let orchestrate_inbound complete successfully and return shipment.
        shipment = orchestrator.orchestrate_inbound(ocr_doc)

        self.assertIsNotNone(shipment)
        self.assertEqual(ocr_doc.processing_status, OCRDocument.ProcessingStatus.COMPLETED)
        # Verify Product was still created
        self.assertTrue(Product.objects.filter(sku='SKU-RAG-01').exists())
        # Verify InboundShipment was still created
        self.assertTrue(InboundShipment.objects.filter(shipment_code='INV-TEST-999').exists())
