import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, StorageAllocation
from apps.warehouse.application.services.digital_twin_sync_service import DigitalTwinSyncService

User = get_user_model()

class DigitalTwinSyncServiceTestCase(TestCase):
    def setUp(self):
        # Clear database
        Bin.objects.all().delete()
        Shelf.objects.all().delete()
        Rack.objects.all().delete()
        Zone.objects.all().delete()
        ZoneGroup.objects.all().delete()
        Warehouse.objects.all().delete()
        Product.objects.all().delete()
        StorageAllocation.objects.all().delete()

        self.client = APIClient()
        self.user = User.objects.create_user(
            username='sync_test_user',
            password='testpassword123',
            email='sync_test@warehouse.com',
            role='STAFF'
        )
        # Login and obtain token
        login_url = reverse('token_obtain_pair')
        res = self.client.post(login_url, {'username': 'sync_test_user', 'password': 'testpassword123'}, format='json')
        self.access_token = res.data['access']
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'}

        # Setup layout structures
        self.warehouse = Warehouse.objects.create(
            name='Sync Test Warehouse',
            location='West Section',
            total_area_sqft=Decimal('5000.00')
        )
        self.zone_group = ZoneGroup.objects.create(
            warehouse=self.warehouse,
            code='ZG-SYNC',
            name='Sync Zone Group',
            zone_group_type='GENERAL_STORAGE'
        )
        self.zone = Zone.objects.create(
            warehouse=self.warehouse,
            zone_group=self.zone_group,
            zone_name='Sync-Zone-1',
            zone_type='GENERAL',
            x=Decimal('10.0'), y=Decimal('10.0'), z=Decimal('0.0'),
            width=Decimal('30.0'), height=Decimal('30.0'), depth=Decimal('15.0')
        )
        self.rack = Rack.objects.create(
            zone=self.zone,
            rack_code='RACK-SYNC-1',
            max_weight=Decimal('2000.00'),
            x=Decimal('12.0'), y=Decimal('12.0'), z=Decimal('0.0'),
            width=Decimal('4.0'), height=Decimal('12.0'), depth=Decimal('2.0'),
            rotation_angle=Decimal('0.0')
        )
        self.shelf = Shelf.objects.create(
            rack=self.rack,
            shelf_number=1,
            max_weight=Decimal('800.00'),
            height_from_ground=Decimal('0.0')
        )
        self.bin_1 = Bin.objects.create(
            shelf=self.shelf,
            bin_code='BIN-SYNC-1-01',
            max_capacity=Decimal('100.00'),
            current_capacity=Decimal('0.00'),
            length=Decimal('50.00'),
            width=Decimal('50.00'),
            height=Decimal('50.00'),
            is_occupied=False
        )
        self.bin_2 = Bin.objects.create(
            shelf=self.shelf,
            bin_code='BIN-SYNC-1-02',
            max_capacity=Decimal('100.00'),
            current_capacity=Decimal('0.00'),
            length=Decimal('50.00'),
            width=Decimal('50.00'),
            height=Decimal('50.00'),
            is_occupied=False
        )

        # Product
        self.category = ProductCategory.objects.create(category_name='Electronics')
        self.product = Product.objects.create(
            sku='SKU-PHONE-XYZ',
            product_name='Smartphone Pro 5G',
            category=self.category,
            weight=Decimal('0.20'),
            is_fragile=False,
            is_hazardous=False
        )

    @patch('channels.layers.get_channel_layer')
    def test_sync_occupancy_updates_metrics_correctly(self, mock_get_channel_layer):
        """Unit test: Verify direct calls to sync_occupancy update database and compute parent metrics."""
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        # Sync bin_1 as occupied with 10 units capacity
        payload = DigitalTwinSyncService.sync_occupancy(
            bin_id=self.bin_1.id,
            is_occupied=True,
            current_capacity=Decimal('10.00')
        )

        # 1. Assert DB states
        self.bin_1.refresh_from_db()
        self.assertTrue(self.bin_1.is_occupied)
        self.assertEqual(self.bin_1.current_capacity, Decimal('10.00'))

        # 2. Assert Dynamic SQL aggregation metrics returned in payload
        # Rack has 2 bins: 1 occupied (bin_1), 1 empty (bin_2) -> 50%
        self.assertEqual(payload['rack']['rack_code'], 'RACK-SYNC-1')
        self.assertEqual(payload['rack']['total_bins'], 2)
        self.assertEqual(payload['rack']['occupied_bins'], 1)
        self.assertEqual(payload['rack']['occupancy_percentage'], 50.0)

        self.assertEqual(payload['zone']['zone_name'], 'Sync-Zone-1')
        self.assertEqual(payload['zone']['total_bins'], 2)
        self.assertEqual(payload['zone']['occupied_bins'], 1)
        self.assertEqual(payload['zone']['occupancy_percentage'], 50.0)

        self.assertEqual(payload['warehouse']['warehouse_name'], 'Sync Test Warehouse')
        self.assertEqual(payload['warehouse']['total_bins'], 2)
        self.assertEqual(payload['warehouse']['occupied_bins'], 1)
        self.assertEqual(payload['warehouse']['occupancy_percentage'], 50.0)

        # 3. Verify WebSocket broadcast payload structure and flat compatibility keys
        mock_channel.group_send.assert_called_once()
        broadcast_args = mock_channel.group_send.call_args[0]
        self.assertEqual(broadcast_args[0], 'occupancy_updates')
        
        msg = broadcast_args[1]['message']
        self.assertEqual(msg['bin_code'], 'BIN-SYNC-1-01')
        self.assertTrue(msg['is_occupied'])
        self.assertEqual(msg['current_capacity'], 10.0)
        self.assertEqual(msg['rack']['occupancy_percentage'], 50.0)
        self.assertEqual(msg['zone']['occupancy_percentage'], 50.0)
        self.assertEqual(msg['warehouse']['occupancy_percentage'], 50.0)

    @patch('channels.layers.get_channel_layer')
    def test_sync_occupancy_keeps_bounds(self, mock_get_channel_layer):
        """Unit test: Verify that current_capacity delta bounds work properly."""
        # 1. Delta cannot drop below 0
        DigitalTwinSyncService.sync_occupancy(
            bin_id=self.bin_2.id,
            is_occupied=False,
            capacity_delta=Decimal('-10.00')
        )
        self.bin_2.refresh_from_db()
        self.assertEqual(self.bin_2.current_capacity, Decimal('0.00'))

        # 2. Delta cannot exceed max_capacity
        DigitalTwinSyncService.sync_occupancy(
            bin_id=self.bin_2.id,
            is_occupied=True,
            capacity_delta=Decimal('150.00')
        )
        self.bin_2.refresh_from_db()
        self.assertEqual(self.bin_2.current_capacity, Decimal('100.00'))

    @patch('apps.inventory.application.services.slotting_service.SlottingService.recommend_storage_location')
    @patch('channels.layers.get_channel_layer')
    def test_allocate_api_integration(self, mock_get_channel_layer, mock_recommend):
        """Integration test: Verify POST /api/recommendations/allocate/ uses DigitalTwinSyncService."""
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        # Mock the recommendation service output
        mock_recommend.return_value = {
            "zone": str(self.zone.id),
            "rack": str(self.rack.id),
            "shelf": str(self.shelf.id),
            "bin": str(self.bin_1.id),
            "bin_code": self.bin_1.bin_code
        }

        url = '/api/recommendations/allocate/'
        payload = {
            'product_id': str(self.product.id),
            'quantity': 5
        }

        response = self.client.post(url, payload, format='json', **self.headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['bin'], str(self.bin_1.id))
        self.assertEqual(response.data['quantity'], 5)

        # Verify DB update of the Bin
        self.bin_1.refresh_from_db()
        self.assertTrue(self.bin_1.is_occupied)
        self.assertEqual(self.bin_1.current_capacity, Decimal('5.00'))

        # Verify StorageAllocation record was created
        allocation = StorageAllocation.objects.get(id=response.data['allocation_id'])
        self.assertEqual(allocation.product, self.product)
        self.assertEqual(allocation.bin, self.bin_1)
        self.assertEqual(allocation.quantity, 5)

        # Verify WebSocket group broadcast was fired with nested structures
        mock_channel.group_send.assert_called_once()
        broadcast_args = mock_channel.group_send.call_args[0]
        self.assertEqual(broadcast_args[0], 'occupancy_updates')
        
        msg = broadcast_args[1]['message']
        self.assertEqual(msg['bin_code'], 'BIN-SYNC-1-01')
        self.assertTrue(msg['is_occupied'])
        self.assertEqual(msg['current_capacity'], 5.0)
        self.assertEqual(msg['rack']['occupancy_percentage'], 50.0)
