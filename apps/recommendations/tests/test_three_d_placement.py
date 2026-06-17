from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, ProductDimension
from apps.recommendations.models.storage_recommendation import StorageRecommendation
from apps.recommendations.models.bin_allocation import BinAllocation
from apps.recommendations.models.bin_3d_placement import Bin3DPlacement
from apps.recommendations.services.three_d_optimization_service import ThreeDOptimizationService

User = get_user_model()

class ThreeDPlacementTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test_3d_user',
            password='test_3d_password',
            email='test_3d@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        # Warehouse layout
        self.warehouse = Warehouse.objects.create(
            name='Primary 3D Warehouse',
            location='Primary Location',
            total_area_sqft=Decimal('2000.00')
        )
        self.zone_group = ZoneGroup.objects.create(
            warehouse=self.warehouse,
            code='A',
            name='Zone Group A',
            zone_group_type='GENERAL_STORAGE'
        )
        self.zone = Zone.objects.create(
            warehouse=self.warehouse,
            zone_group=self.zone_group,
            zone_name='A2',
            zone_type='GENERAL',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0'),
            width=Decimal('10.0'), height=Decimal('10.0'), depth=Decimal('10.0')
        )
        self.rack = Rack.objects.create(
            zone=self.zone,
            rack_code='RACK-3D',
            max_weight=Decimal('500.00'),
            x=Decimal('1.0'), y=Decimal('1.0'), z=Decimal('0.0'),
            width=Decimal('2.0'), height=Decimal('8.0'), depth=Decimal('1.0'),
            rotation_angle=Decimal('0.0')
        )
        self.shelf = Shelf.objects.create(
            rack=self.rack,
            shelf_number=1,
            max_weight=Decimal('100.00'),
            height_from_ground=Decimal('0.5')
        )
        # Bin dimensions: 100 x 80 x 60 (total volume = 480,000)
        self.bin = Bin.objects.create(
            shelf=self.shelf,
            bin_code='BIN-3D-01',
            max_capacity=Decimal('100.00'),
            current_capacity=Decimal('0.00'),
            length=Decimal('100.00'),
            width=Decimal('80.00'),
            height=Decimal('60.00'),
            is_occupied=False
        )

        self.category = ProductCategory.objects.create(category_name='Hardware')
        
        # Product 1: 40 x 30 x 20 (volume = 24,000)
        self.product1 = Product.objects.create(
            category=self.category,
            sku='SKU-PROD1',
            product_name='Router',
            weight=Decimal('2.00')
        )
        self.dimension1 = ProductDimension.objects.create(
            product=self.product1,
            length=Decimal('40.00'),
            width=Decimal('30.00'),
            height=Decimal('20.00'),
            box_length=Decimal('42.00'),
            box_width=Decimal('32.00'),
            box_height=Decimal('22.00')
        )
        self.allocation1 = BinAllocation.objects.create(
            product=self.product1,
            zone_group=self.zone_group,
            zone=self.zone,
            rack=self.rack,
            shelf=self.shelf,
            bin=self.bin,
            allocation_score=0.90,
            allocation_reason='General allocation',
            allocation_source='RULE_ENGINE',
            selected_orientation='40x30x20'
        )

        # Product 2: 30 x 20 x 10 (volume = 6,000)
        self.product2 = Product.objects.create(
            category=self.category,
            sku='SKU-PROD2',
            product_name='Switch',
            weight=Decimal('1.50')
        )
        self.dimension2 = ProductDimension.objects.create(
            product=self.product2,
            length=Decimal('30.00'),
            width=Decimal('20.00'),
            height=Decimal('10.00'),
            box_length=Decimal('32.00'),
            box_width=Decimal('22.00'),
            box_height=Decimal('12.00')
        )
        self.allocation2 = BinAllocation.objects.create(
            product=self.product2,
            zone_group=self.zone_group,
            zone=self.zone,
            rack=self.rack,
            shelf=self.shelf,
            bin=self.bin,
            allocation_score=0.88,
            allocation_reason='General allocation 2',
            allocation_source='RULE_ENGINE',
            selected_orientation='30x20x10'
        )

    def test_single_product_placement_success(self):
        """Test 3D placement logic on an empty bin."""
        # Delete second allocation to test single product in the bin
        self.allocation2.delete()

        service = ThreeDOptimizationService()
        placement = service.evaluate_placement(self.allocation1)

        # Assert correct positioning, volume, and strategy
        self.assertEqual(placement.position_x, Decimal('0.00'))
        self.assertEqual(placement.position_y, Decimal('0.00'))
        self.assertEqual(placement.position_z, Decimal('0.00'))
        self.assertEqual(placement.placement_strategy, Bin3DPlacement.PlacementStrategy.BOTTOM_FLAT)
        
        # Product volume = 40 * 30 * 20 = 24,000
        # Bin volume = 100 * 80 * 60 = 480,000
        # Utilization = (24000 / 480000) * 100 = 5.0%
        self.assertEqual(placement.occupied_volume, Decimal('24000.00'))
        self.assertEqual(placement.remaining_volume, Decimal('456000.00'))
        self.assertEqual(placement.utilization_percentage, Decimal('5.00'))
        self.assertEqual(placement.label_direction, Bin3DPlacement.LabelDirection.FRONT)

    def test_multi_product_packing_coordinates(self):
        """Test multi-product placement shifting coordinates correctly."""
        service = ThreeDOptimizationService()
        # Evaluate first placement
        placement1 = service.evaluate_placement(self.allocation1)
        self.assertEqual(placement1.position_x, Decimal('0.00'))

        # Evaluate second placement
        placement2 = service.evaluate_placement(self.allocation2)

        # First product was 40x30x20 at (0,0,0). Max X bounds is 40.
        # Second product should be placed shifting along X-axis at (40.0, 0.0, 0.0)
        self.assertEqual(placement2.position_x, Decimal('40.00'))
        self.assertEqual(placement2.position_y, Decimal('0.00'))
        self.assertEqual(placement2.position_z, Decimal('0.00'))
        self.assertEqual(placement2.placement_strategy, Bin3DPlacement.PlacementStrategy.CORNER_ALIGN)

        # Volume calculations
        # Product 1: 24,000
        # Product 2: 6,000
        # Total occupied = 30,000
        # Utilization = (30000 / 480000) * 100 = 6.25%
        self.assertEqual(placement2.occupied_volume, Decimal('30000.00'))
        self.assertEqual(placement2.remaining_volume, Decimal('450000.00'))
        self.assertEqual(placement2.utilization_percentage, Decimal('6.25'))

    def test_placement_fails_when_product_too_large(self):
        """Verify ValueError is raised if product doesn't fit in any rotation/layout."""
        # Create a huge product
        huge_product = Product.objects.create(
            category=self.category,
            sku='SKU-HUGE',
            product_name='Warehouse Pallet',
            weight=Decimal('50.00')
        )
        ProductDimension.objects.create(
            product=huge_product,
            length=Decimal('200.00'), # bin length is 100
            width=Decimal('200.00'),
            height=Decimal('200.00'),
            box_length=Decimal('200.00'),
            box_width=Decimal('200.00'),
            box_height=Decimal('200.00')
        )
        huge_allocation = BinAllocation.objects.create(
            product=huge_product,
            zone_group=self.zone_group,
            zone=self.zone,
            rack=self.rack,
            shelf=self.shelf,
            bin=self.bin,
            allocation_score=0.10,
            allocation_reason='Test fail allocation',
            allocation_source='RULE_ENGINE',
            selected_orientation='200x200x200'
        )

        service = ThreeDOptimizationService()
        with self.assertRaises(ValueError):
            service.evaluate_placement(huge_allocation)

    def test_api_three_d_placement_endpoint(self):
        """Test end-to-end API response for 3D placement computation."""
        url = '/api/recommendations/3d-placement/'
        payload = {
            'bin_allocation_id': str(self.allocation1.id)
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data
        self.assertEqual(data['bin_code'], 'BIN-3D-01')
        self.assertEqual(float(data['occupied_volume']), 24000.0)
        self.assertEqual(float(data['remaining_volume']), 456000.0)
        self.assertEqual(float(data['utilization_percentage']), 5.0)
        self.assertEqual(data['placement_strategy'], 'BOTTOM_FLAT')
        self.assertEqual(data['label_direction'], 'FRONT')
        self.assertEqual(float(data['position_x']), 0.0)
        self.assertEqual(float(data['position_y']), 0.0)
        self.assertEqual(float(data['position_z']), 0.0)

        # Check model persistence in DB
        self.assertEqual(Bin3DPlacement.objects.count(), 1)
        placement = Bin3DPlacement.objects.first()
        self.assertEqual(placement.bin_allocation, self.allocation1)
