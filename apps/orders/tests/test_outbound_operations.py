from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from django.utils import timezone

from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin
from apps.warehouse.infrastructure.persistence.models import NavigationNode, StorageLocationNodeMap
from apps.inventory.infrastructure.persistence.models import (
    Product, ProductCategory, ProductDimension, Inventory, StorageAllocation, StockMovement
)
from apps.orders.infrastructure.persistence.models import OutboundShipment
from apps.identity.infrastructure.persistence.models import AuditLog

User = get_user_model()

class OutboundOperationsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test_wms_outbound_user',
            password='test_wms_password',
            email='test_wms_outbound@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        # Build warehouse structure
        self.warehouse = Warehouse.objects.create(
            name='Central Distribution Center',
            location='Avenue A',
            total_area_sqft=Decimal('20000.00')
        )
        self.zone_group = ZoneGroup.objects.create(
            warehouse=self.warehouse,
            code='G2',
            name='General Zone Group',
            zone_group_type='GENERAL_STORAGE'
        )
        self.zone = Zone.objects.create(
            warehouse=self.warehouse,
            zone_group=self.zone_group,
            zone_name='Zone Outbound',
            zone_type='GENERAL',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0'),
            width=Decimal('20.0'), height=Decimal('20.0'), depth=Decimal('20.0')
        )
        self.rack = Rack.objects.create(
            zone=self.zone,
            rack_code='RACK-OB-1',
            max_weight=Decimal('2000.00'),
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0'),
            width=Decimal('3.0'), height=Decimal('10.0'), depth=Decimal('1.5'),
            rotation_angle=Decimal('0.0')
        )
        self.shelf = Shelf.objects.create(
            rack=self.rack,
            shelf_number=1,
            max_weight=Decimal('400.00'),
            height_from_ground=Decimal('0.5')
        )
        self.bin_ob_1 = Bin.objects.create(
            shelf=self.shelf,
            bin_code='BIN-OB-1-01',
            max_capacity=Decimal('100.00'),
            current_capacity=Decimal('30.00'),
            length=Decimal('60.00'),
            width=Decimal('60.00'),
            height=Decimal('60.00'),
            is_occupied=True
        )

        # Setup Product
        self.category = ProductCategory.objects.create(category_name='Hardware')
        self.product = Product.objects.create(
            category=self.category,
            sku='SKU-OB-TOOL',
            product_name='Professional Toolset',
            weight=Decimal('5.50'),
            is_fragile=False,
            is_hazardous=False
        )

        # Add initial inventory allocations
        self.allocation = StorageAllocation.objects.create(
            product=self.product,
            bin=self.bin_ob_1,
            quantity=30
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            total_quantity=30,
            reserved_quantity=0,
            damaged_quantity=0
        )

        # Setup Navigation graph for routing
        self.node_start = NavigationNode.objects.create(
            warehouse=self.warehouse,
            node_name='DOCK_OUTBOUND',
            node_type='DOCK',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0')
        )
        self.node_bin = NavigationNode.objects.create(
            warehouse=self.warehouse,
            node_name='NODE_BIN_OB_1',
            node_type='PICK_POINT',
            x=Decimal('5.0'), y=Decimal('5.0'), z=Decimal('0.0')
        )

        # Connect start node and bin node
        self.node_start.connections = [{"node_id": str(self.node_bin.id), "weight": 7.0}]
        self.node_start.save()
        self.node_bin.connections = [{"node_id": str(self.node_start.id), "weight": 7.0}]
        self.node_bin.save()

        # Create mapping from Bin to Node
        StorageLocationNodeMap.objects.create(
            warehouse=self.warehouse,
            bin=self.bin_ob_1,
            navigation_node=self.node_bin
        )

        # Setup initial OutboundShipment (Order) with items details embedded
        self.shipment = OutboundShipment.objects.create(
            shipment_code='SHIP-OB-1001',
            customer_name='WMS Client Inc.',
            status='CREATED',
            items=[
                {
                    "product_id": str(self.product.id),
                    "quantity": 10,
                    "picked_quantity": 0,
                    "packed_quantity": 0
                }
            ]
        )

    def test_outbound_full_lifecycle_success(self):
        """Test the successful end-to-end outbound operations lifecycle."""
        
        # 1. Generate Pick List
        payload_gen = {'shipment_id': str(self.shipment.id)}
        response_gen = self.client.post('/api/orders/generate-picklist/', payload_gen, format='json')
        self.assertEqual(response_gen.status_code, status.HTTP_200_OK)
        self.assertTrue(response_gen.data['success'])
        self.assertEqual(response_gen.data['status'], 'PENDING')
        self.assertEqual(len(response_gen.data['items']), 1)
        self.assertEqual(response_gen.data['items'][0]['quantity_to_pick'], 10)

        # 2. Assign Picker
        payload_assign = {
            'picklist_id': str(self.shipment.id),
            'operator': 'john_picker'
        }
        response_assign = self.client.post('/api/orders/assign-picker/', payload_assign, format='json')
        self.assertEqual(response_assign.status_code, status.HTTP_200_OK)
        self.assertTrue(response_assign.data['success'])
        self.assertEqual(response_assign.data['status'], 'ASSIGNED')

        # Check Audit Log for Picker Assignment
        self.assertTrue(AuditLog.objects.filter(action_type='PICKER_ASSIGNMENT', record_id=self.shipment.id).exists())

        # 3. Picking Route Optimization
        payload_route = {
            'picklist_id': str(self.shipment.id),
            'start_node_id': str(self.node_start.id)
        }
        response_route = self.client.post('/api/orders/optimize-route/', payload_route, format='json')
        self.assertEqual(response_route.status_code, status.HTTP_200_OK)
        self.assertTrue(response_route.data['success'])
        self.assertGreater(response_route.data['distance'], 0.0)
        self.assertEqual(len(response_route.data['path']), 2)  # DOCK -> BIN

        # 4. Packing Validation
        payload_pack = {
            'picklist_id': str(self.shipment.id),
            'packed_items': [
                {
                    'product_id': str(self.product.id),
                    'quantity': 10
                }
            ]
        }
        response_pack = self.client.post('/api/orders/pack/', payload_pack, format='json')
        self.assertEqual(response_pack.status_code, status.HTTP_200_OK)
        self.assertTrue(response_pack.data['success'])
        self.assertEqual(response_pack.data['status'], 'PACKED')

        # 5. Dispatch Shipment
        payload_dispatch = {'picklist_id': str(self.shipment.id)}
        response_dispatch = self.client.post('/api/orders/dispatch/', payload_dispatch, format='json')
        self.assertEqual(response_dispatch.status_code, status.HTTP_200_OK)
        self.assertTrue(response_dispatch.data['success'])

        # Verify inventory and allocations are decremented
        self.allocation.refresh_from_db()
        self.assertEqual(self.allocation.quantity, 20)

        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.total_quantity, 20)

        # Verify Digital Twin updated bin capacity
        self.bin_ob_1.refresh_from_db()
        self.assertEqual(self.bin_ob_1.current_capacity, Decimal('20.00'))

        # Verify StockMovement generated
        movement = StockMovement.objects.get(product=self.product, movement_type='DISPATCH')
        self.assertEqual(movement.from_bin, self.bin_ob_1)
        self.assertEqual(movement.to_bin, None)
        self.assertEqual(movement.quantity, 10)
        self.assertEqual(movement.operator, 'john_picker')

        # Verify Audit Log
        self.assertTrue(AuditLog.objects.filter(action_type='DISPATCH_ITEM').exists())

        # 6. Shipment Closure
        payload_close = {'picklist_id': str(self.shipment.id)}
        response_close = self.client.post('/api/orders/close/', payload_close, format='json')
        self.assertEqual(response_close.status_code, status.HTTP_200_OK)
        self.assertTrue(response_close.data['success'])
        self.assertEqual(response_close.data['status'], 'CLOSED')
        self.assertIsNotNone(response_close.data['dispatch_time'])

        # Verify final Audit Log
        self.assertTrue(AuditLog.objects.filter(action_type='SHIPMENT_CLOSE', record_id=self.shipment.id).exists())

    def test_generate_picklist_insufficient_stock(self):
        """Test picklist generation fails when requested quantity exceeds available stock."""
        insufficient_shipment = OutboundShipment.objects.create(
            shipment_code='SHIP-OB-SHORT',
            customer_name='Shortage Client',
            status='CREATED',
            items=[
                {
                    "product_id": str(self.product.id),
                    "quantity": 50,  # Only 30 available
                    "picked_quantity": 0,
                    "packed_quantity": 0
                }
            ]
        )
        payload = {'shipment_id': str(insufficient_shipment.id)}
        response = self.client.post('/api/orders/generate-picklist/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', response.data['error'])

    def test_pack_validation_shortage(self):
        """Test packing verification fails when there is a packing shortage."""
        # Generate picklist first
        self.client.post('/api/orders/generate-picklist/', {'shipment_id': str(self.shipment.id)}, format='json')

        # Try to pack with shortage
        payload = {
            'picklist_id': str(self.shipment.id),
            'packed_items': [
                {
                    'product_id': str(self.product.id),
                    'quantity': 5  # Picklist expects 10
                }
            ]
        }
        response = self.client.post('/api/orders/pack/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Packing shortage', response.data['error'])

    def test_dispatch_fails_before_packed(self):
        """Test dispatch operations fail if shipment is not in PACKED state."""
        # Generate picklist and assign picker, but don't pack
        self.client.post('/api/orders/generate-picklist/', {'shipment_id': str(self.shipment.id)}, format='json')
        self.client.post('/api/orders/assign-picker/', {'picklist_id': str(self.shipment.id), 'operator': 'jack'}, format='json')

        payload = {'picklist_id': str(self.shipment.id)}
        response = self.client.post('/api/orders/dispatch/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('must be PACKED to dispatch', response.data['error'])
