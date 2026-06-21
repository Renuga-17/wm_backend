from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, ProductDimension
from apps.recommendations.models.storage_recommendation import StorageRecommendation
from apps.recommendations.models.product_classification import ProductClassification
from apps.recommendations.models.recommendation_rule import RecommendationRule
from apps.recommendations.models.bin_allocation import BinAllocation
from apps.recommendations.models.bin_3d_placement import Bin3DPlacement
from apps.recommendations.services.storage_recommendation_service import StorageRecommendationService
from apps.recommendations.services.bin_allocation_service import BinAllocationService
from apps.recommendations.services.three_d_optimization_service import ThreeDOptimizationService

User = get_user_model()

class ProductDimensionAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test_wms_user',
            password='test_wms_password',
            email='test_wms@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        self.category = ProductCategory.objects.create(category_name='Logistics')
        self.product = Product.objects.create(
            category=self.category,
            sku='SKU-LAPTOP-01',
            product_name='Premium Laptop',
            weight=Decimal('3.50'),
            is_fragile=True,
            is_hazardous=False
        )

        self.dimension = ProductDimension.objects.create(
            product=self.product,
            length=Decimal('40.00'),
            width=Decimal('30.00'),
            height=Decimal('20.00'),
            box_length=Decimal('42.00'),
            box_width=Decimal('32.00'),
            box_height=Decimal('22.00')
        )

        self.list_url = '/api/product-dimensions/'
        self.detail_url = f'/api/product-dimensions/{self.dimension.id}/'

    def test_list_dimensions(self):
        """Test GET list of dimensions."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(str(response.data['results'][0]['product']), str(self.product.id))

    def test_retrieve_dimension(self):
        """Test GET single dimension."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['product']), str(self.product.id))
        self.assertEqual(float(response.data['length']), 40.0)

    def test_create_dimension_success(self):
        """Test POST create dimension."""
        product_new = Product.objects.create(
            category=self.category,
            sku='SKU-PHONE-01',
            product_name='Smartphone',
            weight=Decimal('0.50'),
            is_fragile=False,
            is_hazardous=False
        )
        payload = {
            'product': str(product_new.id),
            'length': '15.00',
            'width': '8.00',
            'height': '1.50',
            'box_length': '17.00',
            'box_width': '10.00',
            'box_height': '3.00'
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductDimension.objects.count(), 2)

    def test_create_dimension_invalid_values(self):
        """Test POST create dimension with non-positive values fails validation."""
        product_new = Product.objects.create(
            category=self.category,
            sku='SKU-PHONE-01',
            product_name='Smartphone',
            weight=Decimal('0.50'),
            is_fragile=False,
            is_hazardous=False
        )
        # Length <= 0
        payload = {
            'product': str(product_new.id),
            'length': '0.00',
            'width': '8.00',
            'height': '1.50',
            'box_length': '17.00',
            'box_width': '10.00',
            'box_height': '3.00'
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('length', response.data)

        # Height negative
        payload = {
            'product': str(product_new.id),
            'length': '15.00',
            'width': '8.00',
            'height': '-1.50',
            'box_length': '17.00',
            'box_width': '10.00',
            'box_height': '3.00'
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('height', response.data)

    def test_update_dimension(self):
        """Test PATCH update dimension."""
        payload = {
            'length': '45.00'
        }
        response = self.client.patch(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dimension.refresh_from_db()
        self.assertEqual(self.dimension.length, Decimal('45.00'))

    def test_delete_dimension(self):
        """Test DELETE dimension."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProductDimension.objects.count(), 0)


class IntegrationValidationTestCase(TestCase):
    def setUp(self):
        # Base setup identical to BinAllocationTestCase for full verification
        self.warehouse = Warehouse.objects.create(
            name='Primary Warehouse',
            location='Aisle A',
            total_area_sqft=Decimal('5000.00')
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
            rack_code='RACK-A2-1',
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
        self.bin = Bin.objects.create(
            shelf=self.shelf,
            bin_code='BIN-A2-1-01',
            max_capacity=Decimal('10.00'),
            current_capacity=Decimal('1.00'),
            length=Decimal('50.00'),
            width=Decimal('40.00'),
            height=Decimal('30.00'),
            is_occupied=False
        )
        self.category = ProductCategory.objects.create(category_name='Logistics')
        self.product = Product.objects.create(
            category=self.category,
            sku='SKU-LAPTOP-01',
            product_name='Premium Laptop',
            weight=Decimal('3.50'),
            is_fragile=True,
            is_hazardous=False
        )
        self.dimension = ProductDimension.objects.create(
            product=self.product,
            length=Decimal('40.00'),
            width=Decimal('30.00'),
            height=Decimal('20.00'),
            box_length=Decimal('42.00'),
            box_width=Decimal('32.00'),
            box_height=Decimal('22.00')
        )
        
        # Classification required for recommendation
        self.classification = ProductClassification.objects.create(
            product=self.product,
            movement_type=RecommendationRule.MovementType.FAST,
            storage_type=RecommendationRule.StorageType.GENERAL
        )
        
        # Rule required for zone group matching
        self.rule = RecommendationRule.objects.create(
            movement_type=RecommendationRule.MovementType.FAST,
            storage_type=RecommendationRule.StorageType.GENERAL,
            zone_group_type=RecommendationRule.ZoneGroupType.GENERAL_STORAGE,
            priority=10
        )

    def test_downstream_integration(self):
        """
        Verify that created classification and dimensions flow correctly through:
        1. Storage Recommendation Engine
        2. Bin Allocation Engine
        3. 3D Optimization Engine
        """
        # Step 1: Run Storage Recommendation Engine
        rec_service = StorageRecommendationService()
        recommendation = rec_service.generate_recommendation(self.product.id)
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.product, self.product)
        self.assertEqual(recommendation.zone, self.zone)
        self.assertEqual(recommendation.zone_group, self.zone_group)

        # Step 2: Run Bin Allocation Engine (consumes dimension and storage recommendation)
        alloc_service = BinAllocationService()
        allocation = alloc_service.generate_bin_allocation(self.product.id)
        self.assertIsNotNone(allocation)
        self.assertEqual(allocation.product, self.product)
        self.assertEqual(allocation.bin, self.bin)
        self.assertEqual(allocation.selected_orientation, '40x30x20')

        # Step 3: Run 3D Optimization Engine (consumes dimension and bin allocation)
        three_d_service = ThreeDOptimizationService()
        placement = three_d_service.evaluate_placement(allocation)
        self.assertIsNotNone(placement)
        self.assertEqual(placement.bin_allocation, allocation)
        self.assertEqual(placement.position_x, Decimal('0.00'))
        self.assertEqual(placement.position_y, Decimal('0.00'))
        self.assertEqual(placement.position_z, Decimal('0.00'))
        self.assertEqual(placement.placement_strategy, Bin3DPlacement.PlacementStrategy.BOTTOM_FLAT)
