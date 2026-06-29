from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from django.utils import timezone

from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin
from apps.inventory.infrastructure.persistence.models import (
    Product, ProductCategory, ProductDimension, Inventory, StorageAllocation, StockMovement
)
from apps.identity.infrastructure.persistence.models import AuditLog
from apps.recommendations.models.bin_allocation import BinAllocation

User = get_user_model()

class InventoryOperationsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test_wms_user',
            password='test_wms_password',
            email='test_wms@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        # Build warehouse structure
        self.warehouse = Warehouse.objects.create(
            name='Central Warehouse',
            location='Main Blvd',
            total_area_sqft=Decimal('10000.00')
        )
        self.zone_group = ZoneGroup.objects.create(
            warehouse=self.warehouse,
            code='G1',
            name='Zone Group 1',
            zone_group_type='GENERAL_STORAGE'
        )
        self.zone = Zone.objects.create(
            warehouse=self.warehouse,
            zone_group=self.zone_group,
            zone_name='Zone A',
            zone_type='GENERAL',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0'),
            width=Decimal('20.0'), height=Decimal('20.0'), depth=Decimal('20.0')
        )
        self.rack = Rack.objects.create(
            zone=self.zone,
            rack_code='RACK-A-1',
            max_weight=Decimal('1000.00'),
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0'),
            width=Decimal('3.0'), height=Decimal('10.0'), depth=Decimal('1.5'),
            rotation_angle=Decimal('0.0')
        )
        self.shelf = Shelf.objects.create(
            rack=self.rack,
            shelf_number=1,
            max_weight=Decimal('200.00'),
            height_from_ground=Decimal('0.5')
        )
        self.bin_from = Bin.objects.create(
            shelf=self.shelf,
            bin_code='BIN-A-1-01',
            max_capacity=Decimal('100.00'),
            current_capacity=Decimal('20.00'),
            length=Decimal('60.00'),
            width=Decimal('60.00'),
            height=Decimal('60.00'),
            is_occupied=True
        )
        self.bin_to = Bin.objects.create(
            shelf=self.shelf,
            bin_code='BIN-A-1-02',
            max_capacity=Decimal('100.00'),
            current_capacity=Decimal('0.00'),
            length=Decimal('60.00'),
            width=Decimal('60.00'),
            height=Decimal('60.00'),
            is_occupied=False
        )

        # Setup Product
        self.category = ProductCategory.objects.create(category_name='Electronics')
        self.product = Product.objects.create(
            category=self.category,
            sku='SKU-PHONE-XYZ',
            product_name='Smartphone XYZ',
            weight=Decimal('0.50'),
            is_fragile=False,
            is_hazardous=False
        )
        self.dimension = ProductDimension.objects.create(
            product=self.product,
            length=Decimal('15.00'),
            width=Decimal('8.00'),
            height=Decimal('2.00'),
            box_length=Decimal('17.00'),
            box_width=Decimal('10.00'),
            box_height=Decimal('4.00')
        )

        # Add initial inventory and allocations
        self.allocation = StorageAllocation.objects.create(
            product=self.product,
            bin=self.bin_from,
            quantity=20
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            total_quantity=20,
            reserved_quantity=0,
            damaged_quantity=0
        )

        # Add initial BinAllocation recommendation record
        self.bin_alloc = BinAllocation.objects.create(
            product=self.product,
            zone_group=self.zone_group,
            zone=self.zone,
            rack=self.rack,
            shelf=self.shelf,
            bin=self.bin_from,
            allocation_score=0.95,
            allocation_reason='Optimal match',
            selected_orientation='L×W×H',
            storage_status=BinAllocation.StorageStatus.STORED,
            stored_at=timezone.now(),
            operator='system'
        )

    def test_relocate_success_full(self):
        """Test successful relocation of all stock from one bin to another."""
        payload = {
            'product_id': str(self.product.id),
            'from_bin_id': str(self.bin_from.id),
            'to_bin_id': str(self.bin_to.id),
            'quantity': 20,
            'operator': 'admin_user'
        }
        response = self.client.post('/api/inventory/relocate/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # Verify allocations updated
        self.assertFalse(StorageAllocation.objects.filter(bin=self.bin_from).exists())
        to_alloc = StorageAllocation.objects.get(bin=self.bin_to, product=self.product)
        self.assertEqual(to_alloc.quantity, 20)

        # Verify global Inventory remains unchanged
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.total_quantity, 20)

        # Verify digital twin updated
        self.bin_from.refresh_from_db()
        self.bin_to.refresh_from_db()
        self.assertEqual(self.bin_from.current_capacity, Decimal('0.00'))
        self.assertFalse(self.bin_from.is_occupied)
        self.assertEqual(self.bin_to.current_capacity, Decimal('20.00'))
        self.assertTrue(self.bin_to.is_occupied)

        # Verify recommendation status updated
        self.bin_alloc.refresh_from_db()
        self.assertEqual(self.bin_alloc.storage_status, BinAllocation.StorageStatus.ALLOCATED)
        to_bin_alloc = BinAllocation.objects.filter(bin=self.bin_to, product=self.product).first()
        self.assertIsNotNone(to_bin_alloc)
        self.assertEqual(to_bin_alloc.storage_status, BinAllocation.StorageStatus.STORED)

        # Verify stock movement record created
        movement = StockMovement.objects.get(product=self.product, movement_type='RELOCATION')
        self.assertEqual(movement.from_bin, self.bin_from)
        self.assertEqual(movement.to_bin, self.bin_to)
        self.assertEqual(movement.quantity, 20)
        self.assertEqual(movement.operator, 'admin_user')

        # Verify audit log created
        audit = AuditLog.objects.filter(action_type='RELOCATION').first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.user, self.user)

    def test_relocate_success_partial(self):
        """Test successful relocation of partial stock from one bin to another."""
        payload = {
            'product_id': self.product.sku,  # Test using SKU resolution
            'from_bin_id': self.bin_from.bin_code,  # Test using bin_code resolution
            'to_bin_id': self.bin_to.bin_code,
            'quantity': 5,
            'operator': 'helper_user'
        }
        response = self.client.post('/api/inventory/relocate/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify source and target allocations
        from_alloc = StorageAllocation.objects.get(bin=self.bin_from, product=self.product)
        self.assertEqual(from_alloc.quantity, 15)
        to_alloc = StorageAllocation.objects.get(bin=self.bin_to, product=self.product)
        self.assertEqual(to_alloc.quantity, 5)

        # Verify bin capacity changes
        self.bin_from.refresh_from_db()
        self.bin_to.refresh_from_db()
        self.assertEqual(self.bin_from.current_capacity, Decimal('15.00'))
        self.assertTrue(self.bin_from.is_occupied)
        self.assertEqual(self.bin_to.current_capacity, Decimal('5.00'))
        self.assertTrue(self.bin_to.is_occupied)

        # Verify BinAllocation status stays STORED on source and becomes STORED on target
        self.bin_alloc.refresh_from_db()
        self.assertEqual(self.bin_alloc.storage_status, BinAllocation.StorageStatus.STORED)
        to_bin_alloc = BinAllocation.objects.filter(bin=self.bin_to, product=self.product).first()
        self.assertIsNotNone(to_bin_alloc)
        self.assertEqual(to_bin_alloc.storage_status, BinAllocation.StorageStatus.STORED)

    def test_relocate_capacity_overflow(self):
        """Test relocation fails if target bin capacity is exceeded."""
        self.bin_to.max_capacity = Decimal('10.00')
        self.bin_to.save()

        payload = {
            'product_id': str(self.product.id),
            'from_bin_id': str(self.bin_from.id),
            'to_bin_id': str(self.bin_to.id),
            'quantity': 15,
        }
        response = self.client.post('/api/inventory/relocate/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('capacity exceeded', response.data['error'])

    def test_relocate_dimensions_mismatch(self):
        """Test relocation fails if product dimensions are too large for the target bin."""
        # Make bin extremely small in all dimensions
        self.bin_to.length = Decimal('1.00')
        self.bin_to.width = Decimal('1.00')
        self.bin_to.height = Decimal('1.00')
        self.bin_to.save()

        payload = {
            'product_id': str(self.product.id),
            'from_bin_id': str(self.bin_from.id),
            'to_bin_id': str(self.bin_to.id),
            'quantity': 5,
        }
        response = self.client.post('/api/inventory/relocate/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('dimensions do not fit', response.data['error'])

    def test_relocate_weight_overflow(self):
        """Test relocation fails if shelf or rack weight limits are exceeded."""
        # Set max shelf weight to very low
        self.shelf.max_weight = Decimal('5.00')
        self.shelf.save()

        # Product weight is 0.5. Relocating 20 units is 10.0 weight.
        # But wait! They are on the same shelf (bin_from and bin_to are on self.shelf).
        # Since they are on the same shelf, the view code compensates:
        # projected_shelf_weight = shelf_weight (which already includes the 20 * 0.5 = 10.0 weight).
        # Let's test that intra-shelf relocation does not fail because of weight compensation!
        payload = {
            'product_id': str(self.product.id),
            'from_bin_id': str(self.bin_from.id),
            'to_bin_id': str(self.bin_to.id),
            'quantity': 20,
        }
        response = self.client.post('/api/inventory/relocate/', payload, format='json')
        # This should fail only if projected weight exceeds max_weight.
        # Here, shelf_weight is 10.0, max_weight is 5.0. 10.0 > 5.0, so it fails.
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Now, set shelf max_weight to 15.0. Total shelf weight is 10.0.
        # If we relocate 10 units, intra-shelf moves shouldn't double count!
        self.shelf.max_weight = Decimal('15.00')
        self.shelf.save()

        response = self.client.post('/api/inventory/relocate/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_bin_transfer_success(self):
        """Test the bin transfer action, which mirrors relocate and performs full validation."""
        payload = {
            'product_id': str(self.product.id),
            'from_bin_id': str(self.bin_from.id),
            'to_bin_id': str(self.bin_to.id),
            'quantity': 10,
            'operator': 'transfer_op'
        }
        response = self.client.post('/api/inventory/transfer/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # Check movement type is BIN_TRANSFER
        movement = StockMovement.objects.get(product=self.product, movement_type='BIN_TRANSFER')
        self.assertEqual(movement.quantity, 10)
        self.assertEqual(movement.operator, 'transfer_op')

    def test_stock_adjustment_increase(self):
        """Test positive stock adjustment."""
        payload = {
            'product_id': str(self.product.id),
            'bin_id': str(self.bin_from.id),
            'quantity': 10,
            'reason': 'Found inventory',
            'operator': 'audit_op'
        }
        response = self.client.post('/api/inventory/adjust/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify StorageAllocation increased
        alloc = StorageAllocation.objects.get(bin=self.bin_from, product=self.product)
        self.assertEqual(alloc.quantity, 30)

        # Verify global Inventory total increased
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.total_quantity, 30)

        # Verify capacity increased
        self.bin_from.refresh_from_db()
        self.assertEqual(self.bin_from.current_capacity, Decimal('30.00'))

        # Verify movement
        movement = StockMovement.objects.get(product=self.product, movement_type='STOCK_ADJUSTMENT_INCREASE')
        self.assertEqual(movement.quantity, 10)
        self.assertIn('Found inventory', movement.operator)

    def test_stock_adjustment_decrease(self):
        """Test negative stock adjustment."""
        payload = {
            'product_id': str(self.product.id),
            'bin_id': str(self.bin_from.id),
            'quantity': -5,
            'reason': 'Lost items',
            'operator': 'audit_op'
        }
        response = self.client.post('/api/inventory/adjust/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify StorageAllocation decreased
        alloc = StorageAllocation.objects.get(bin=self.bin_from, product=self.product)
        self.assertEqual(alloc.quantity, 15)

        # Verify global Inventory decreased
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.total_quantity, 15)

        # Verify capacity decreased
        self.bin_from.refresh_from_db()
        self.assertEqual(self.bin_from.current_capacity, Decimal('15.00'))

        # Verify movement
        movement = StockMovement.objects.get(product=self.product, movement_type='STOCK_ADJUSTMENT_DECREASE')
        self.assertEqual(movement.quantity, 5)
        self.assertIn('Lost items', movement.operator)

    def test_stock_adjustment_prevent_negative(self):
        """Test stock adjustment fails if it tries to reduce below zero."""
        payload = {
            'product_id': str(self.product.id),
            'bin_id': str(self.bin_from.id),
            'quantity': -25,
        }
        response = self.client.post('/api/inventory/adjust/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot adjust below zero', response.data['error'])

    def test_report_damage_success(self):
        """Test damage reporting decreases good inventory and increases damaged inventory."""
        payload = {
            'product_id': str(self.product.id),
            'bin_id': str(self.bin_from.id),
            'quantity': 5,
            'reason': 'Dropped package',
            'operator': 'handling_op'
        }
        response = self.client.post('/api/inventory/report-damage/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify good stock allocation decreased
        alloc = StorageAllocation.objects.get(bin=self.bin_from, product=self.product)
        self.assertEqual(alloc.quantity, 15)

        # Verify global Inventory: total reduced by 5, damaged increased by 5
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.total_quantity, 15)
        self.assertEqual(self.inventory.damaged_quantity, 5)

        # Verify capacity decreased (damaged stock is removed from physical bin layout)
        self.bin_from.refresh_from_db()
        self.assertEqual(self.bin_from.current_capacity, Decimal('15.00'))

        # Verify movement
        movement = StockMovement.objects.get(product=self.product, movement_type='DAMAGE_REPORT')
        self.assertEqual(movement.quantity, 5)

    def test_report_damage_insufficient_stock(self):
        """Test reporting damage fails if there is insufficient stock in the specified bin."""
        payload = {
            'product_id': str(self.product.id),
            'bin_id': str(self.bin_from.id),
            'quantity': 30,
        }
        response = self.client.post('/api/inventory/report-damage/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', response.data['error'])

    def test_audit_no_variance(self):
        """Test stocktake audit with no variance between physical and system count."""
        payload = {
            'product_id': str(self.product.id),
            'bin_id': str(self.bin_from.id),
            'physical_count': 20,
            'operator': 'audit_op'
        }
        response = self.client.post('/api/inventory/audit/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'reconciled')
        self.assertEqual(response.data['variance'], 0)

        # Check allocations unchanged
        alloc = StorageAllocation.objects.get(bin=self.bin_from, product=self.product)
        self.assertEqual(alloc.quantity, 20)

    def test_audit_reconcile_variance(self):
        """Test stocktake audit with variance corrects storage and global quantities."""
        payload = {
            'product_id': str(self.product.id),
            'bin_id': str(self.bin_from.id),
            'physical_count': 25,  # Variance of +5
            'operator': 'audit_op'
        }
        response = self.client.post('/api/inventory/audit/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'adjusted')
        self.assertEqual(response.data['variance'], 5)

        # Check allocations updated
        alloc = StorageAllocation.objects.get(bin=self.bin_from, product=self.product)
        self.assertEqual(alloc.quantity, 25)

        # Check global inventory updated
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.total_quantity, 25)

        # Check bin capacity updated
        self.bin_from.refresh_from_db()
        self.assertEqual(self.bin_from.current_capacity, Decimal('25.00'))

        # Check movement type is AUDIT_SURPLUS
        movement = StockMovement.objects.get(product=self.product, movement_type='AUDIT_SURPLUS')
        self.assertEqual(movement.quantity, 5)
