import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.recommendations.models.bin_allocation import BinAllocation
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, Inventory, StockMovement
from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin

User = get_user_model()



class StorageCompletionTestCase(TestCase):
    def setUp(self):
        # Clear database records
        BinAllocation.objects.all().delete()
        StockMovement.objects.all().delete()
        Inventory.objects.all().delete()
        Product.objects.all().delete()

        self.client = APIClient()
        self.user = User.objects.create_user(
            username='completion_test_user',
            password='testpassword123',
            email='completion_test@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        # Setup spatial graph
        self.warehouse = Warehouse.objects.create(
            name='Test Completion Warehouse',
            location='Aisle 1',
            total_area_sqft=Decimal('2000.00')
        )
        self.zone_group = ZoneGroup.objects.create(
            warehouse=self.warehouse,
            code='G2',
            name='General Group 2',
            zone_group_type='GENERAL_STORAGE'
        )
        self.zone = Zone.objects.create(
            warehouse=self.warehouse,
            zone_group=self.zone_group,
            zone_name='Zone-G2',
            zone_type='GENERAL',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0'),
            width=Decimal('20.0'), height=Decimal('20.0'), depth=Decimal('20.0')
        )
        self.rack = Rack.objects.create(
            zone=self.zone,
            rack_code='RACK-G2-1',
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
            bin_code='BIN-G2-1-01',
            max_capacity=Decimal('50.00'),
            current_capacity=Decimal('0.00'),
            length=Decimal('100.00'),
            width=Decimal('100.00'),
            height=Decimal('100.00'),
            is_occupied=False
        )

        # Product
        self.category = ProductCategory.objects.create(category_name='Hardware')
        self.product = Product.objects.create(
            sku='SKU-HDD-99',
            product_name='1TB SSD Solid State Drive',
            category=self.category,
            weight=0.15,
            is_fragile=False,
            is_hazardous=False
        )

        # Base Bin Allocation
        self.allocation = BinAllocation.objects.create(
            product=self.product,
            zone_group=self.zone_group,
            zone=self.zone,
            rack=self.rack,
            shelf=self.shelf,
            bin=self.bin,
            allocation_score=0.98,
            allocation_reason='Nearest general bin',
            selected_orientation='Front'
        )

    @patch('django.db.models.signals.post_save.send')
    @patch('channels.layers.get_channel_layer')
    def test_storage_completion_success(self, mock_get_channel_layer, mock_post_save):
        """Test a valid patch request marks storage complete and syncs state."""
        # Mock WebSocket channel layer
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        url = f'/api/recommendations/bin-allocation/{self.allocation.id}/complete/'
        payload = {'operator': 'completion_op_99'}

        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['storage_status'], 'STORED')
        self.assertEqual(response.data['operator'], 'completion_op_99')
        self.assertIsNotNone(response.data['stored_at'])

        # Verify BinAllocation is updated
        self.allocation.refresh_from_db()
        self.assertEqual(self.allocation.storage_status, BinAllocation.StorageStatus.STORED)
        self.assertEqual(self.allocation.operator, 'completion_op_99')

        # Verify Bin is updated
        self.bin.refresh_from_db()
        self.assertTrue(self.bin.is_occupied)

        # Verify Inventory total quantity is increased
        inventory = Inventory.objects.get(product=self.product)
        self.assertEqual(inventory.total_quantity, 1)

        # Verify StockMovement logging
        movement = StockMovement.objects.get(product=self.product)
        self.assertEqual(movement.movement_type, 'INBOUND_STORAGE_COMPLETED')
        self.assertEqual(movement.to_bin, self.bin)
        self.assertIsNone(movement.from_bin)
        self.assertEqual(movement.quantity, 1)
        self.assertEqual(movement.operator, 'completion_op_99')

        # Verify WebSocket group broadcast was fired
        mock_channel.group_send.assert_called_once()
        broadcast_args = mock_channel.group_send.call_args[0]
        self.assertEqual(broadcast_args[0], 'occupancy_updates')
        self.assertEqual(broadcast_args[1]['type'], 'occupancy_message')
        self.assertEqual(broadcast_args[1]['message']['bin_code'], self.bin.bin_code)
        self.assertTrue(broadcast_args[1]['message']['is_occupied'])

    def test_duplicate_completion_raises_error(self):
        """Test trying to complete an already stored allocation raises 400."""
        self.allocation.storage_status = BinAllocation.StorageStatus.STORED
        self.allocation.save()

        url = f'/api/recommendations/bin-allocation/{self.allocation.id}/complete/'
        response = self.client.patch(url, {'operator': 'op_test'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already completed", response.data['error'])

    def test_missing_operator_raises_error(self):
        """Test missing operator payload returns 400."""
        url = f'/api/recommendations/bin-allocation/{self.allocation.id}/complete/'
        response = self.client.patch(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("operator is required", response.data['error'])

        # Verify database is unchanged
        self.allocation.refresh_from_db()
        self.assertEqual(self.allocation.storage_status, BinAllocation.StorageStatus.ALLOCATED)

        self.bin.refresh_from_db()
        self.assertFalse(self.bin.is_occupied)

        self.assertFalse(Inventory.objects.filter(product=self.product).exists())
        self.assertFalse(StockMovement.objects.filter(product=self.product).exists())

    def test_invalid_uuid_returns_404(self):
        """Test calling complete on non-existent allocation integer ID returns 404."""
        non_existent_id = 99999
        url = f'/api/recommendations/bin-allocation/{non_existent_id}/complete/'
        response = self.client.patch(url, {'operator': 'op_test'}, format='json')
    
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.inventory.infrastructure.persistence.models.StockMovement.objects.create')
    def test_transaction_rollback_on_failure(self, mock_movement_create):
        """Test that if a downstream creation fails, the database rolls back to original state."""
        # Force StockMovement creation to raise an exception
        mock_movement_create.side_effect = Exception("Simulated DB integrity failure")

        url = f'/api/recommendations/bin-allocation/{self.allocation.id}/complete/'
        response = self.client.patch(url, {'operator': 'op_fail'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Assert database was fully rolled back
        self.allocation.refresh_from_db()
        self.assertEqual(self.allocation.storage_status, BinAllocation.StorageStatus.ALLOCATED)
        self.assertIsNone(self.allocation.stored_at)

        self.bin.refresh_from_db()
        self.assertFalse(self.bin.is_occupied)

        # Inventory record must either not exist or be 0
        self.assertFalse(Inventory.objects.filter(product=self.product).exists())
