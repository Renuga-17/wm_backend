from typing import cast
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.response import Response
from decimal import Decimal

from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, ProductDimension
from apps.recommendations.models.storage_recommendation import StorageRecommendation
from apps.recommendations.models.bin_allocation import BinAllocation
from apps.recommendations.services.bin_allocation_service import BinAllocationService

User = get_user_model()

class BinAllocationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(  # type: ignore
            username='test_wms_user',
            password='test_wms_password',
            email='test_wms@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        # Base Test Data
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

        self.category = ProductCategory.objects.create(
            category_name='Logistics'
        )

        self.product = Product.objects.create(
            category=self.category,
            sku='SKU-LAPTOP-01',
            product_name='Premium Laptop',
            weight=Decimal('3.50'),
            is_fragile=True,
            is_hazardous=False
        )

        # Product dimensions: fits originally (e.g. 40x30x20)
        self.dimension = ProductDimension.objects.create(
            product=self.product,
            length=Decimal('40.00'),
            width=Decimal('30.00'),
            height=Decimal('20.00'),
            box_length=Decimal('42.00'),
            box_width=Decimal('32.00'),
            box_height=Decimal('22.00')
        )

        # Recommendation for product in Zone A2
        self.recommendation = StorageRecommendation.objects.create(
            product=self.product,
            zone_group=self.zone_group,
            zone=self.zone,
            recommendation_reason='Optimal zone based on rule engine',
            recommendation_score=0.95,
            recommendation_source=StorageRecommendation.RecommendationSource.RULE_ENGINE,
            recommendation_version='v1'
        )

    def test_bin_allocation_success(self):
        """Test happy path for bin allocation API."""
        url = '/api/recommendations/bin-allocation/'
        response = cast(Response, self.client.post(url, {'product_id': str(self.product.id)}, format='json'))
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert response.data is not None
        data = response.data
        self.assertEqual(data['product_id'], str(self.product.id))
        self.assertEqual(data['zone_group'], 'A')
        self.assertEqual(data['zone'], 'A2')
        self.assertEqual(data['rack']['code'], 'RACK-A2-1')
        self.assertEqual(data['shelf']['number'], 1)
        self.assertEqual(data['bin']['code'], 'BIN-A2-1-01')
        self.assertEqual(data['selected_orientation'], '40x30x20')
        self.assertTrue(data['allocation_score'] > 0.0)
        self.assertEqual(data['allocation_source'], 'RULE_ENGINE')
        self.assertEqual(data['allocation_version'], 'v1')

        # Check persistence
        self.assertEqual(BinAllocation.objects.count(), 1)
        alloc = BinAllocation.objects.first()
        assert alloc is not None
        self.assertEqual(alloc.product, self.product)
        self.assertEqual(alloc.bin, self.bin)
        self.assertEqual(alloc.selected_orientation, '40x30x20')

    def test_missing_product_dimensions(self):
        """Test error when product dimension is missing."""
        # Delete dimensions
        ProductDimension.objects.filter(product=self.product).delete()

        url = '/api/recommendations/bin-allocation/'
        response = cast(Response, self.client.post(url, {'product_id': str(self.product.id)}, format='json'))
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert response.data is not None
        self.assertIn("dimensions not found", response.data['error'].lower())

    def test_dimension_mismatch(self):
        """Test error when product dimensions exceed bin dimensions in all orientations."""
        # Update product dimensions to be huge
        self.dimension.length = Decimal('100.00')
        self.dimension.width = Decimal('100.00')
        self.dimension.height = Decimal('100.00')
        self.dimension.save()

        url = '/api/recommendations/bin-allocation/'
        response = cast(Response, self.client.post(url, {'product_id': str(self.product.id)}, format='json'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert response.data is not None
        self.assertIn("no candidate bins met dimension and capacity constraints", response.data['error'].lower())

    def test_orientation_selection(self):
        """
        Product dimensions: 40x30x20
        Bin dimensions: 25x45x35
        Only fits after rotation (e.g. 20x40x30).
        Verify correct orientation is selected and persisted.
        """
        # Set bin dimensions so L=25, W=45, H=35
        self.bin.length = Decimal('25.00')
        self.bin.width = Decimal('45.00')
        self.bin.height = Decimal('35.00')
        self.bin.save()

        # The product (40, 30, 20) does not fit originally because L=40 > bin L=25.
        # But rotated as 20x40x30: 20 <= 25, 40 <= 45, 30 <= 35 -> fits!
        
        url = '/api/recommendations/bin-allocation/'
        response = cast(Response, self.client.post(url, {'product_id': str(self.product.id)}, format='json'))
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert response.data is not None
        data = response.data
        self.assertEqual(data['selected_orientation'], '20x40x30')
        
        alloc = BinAllocation.objects.first()
        assert alloc is not None
        self.assertEqual(alloc.selected_orientation, '20x40x30')

    def test_weight_exceeds_rack_capacity(self):
        """Test error when product weight exceeds rack maximum capacity."""
        # Set rack max weight to small value
        self.rack.max_weight = Decimal('2.00')  # product is 3.50
        self.rack.save()

        url = '/api/recommendations/bin-allocation/'
        response = cast(Response, self.client.post(url, {'product_id': str(self.product.id)}, format='json'))
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert response.data is not None
        self.assertIn("weight capacity exceeded", response.data['error'].lower())

    def test_weight_exceeds_shelf_capacity(self):
        """Test error when product weight exceeds shelf maximum capacity."""
        # Set shelf max weight to small value
        self.shelf.max_weight = Decimal('2.00')  # product is 3.50
        self.shelf.save()

        url = '/api/recommendations/bin-allocation/'
        response = cast(Response, self.client.post(url, {'product_id': str(self.product.id)}, format='json'))
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert response.data is not None
        self.assertIn("weight capacity exceeded", response.data['error'].lower())

    def test_bin_capacity_exceeded(self):
        """Test error when bin capacity is exceeded."""
        # Make bin occupied or at max capacity
        self.bin.current_capacity = self.bin.max_capacity
        self.bin.save()

        url = '/api/recommendations/bin-allocation/'
        response = cast(Response, self.client.post(url, {'product_id': str(self.product.id)}, format='json'))
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert response.data is not None
        self.assertIn("no candidate bins met dimension and capacity constraints", response.data['error'].lower())

    def test_verify_latest_recommendation_used(self):
        """Verify that the latest StorageRecommendation (by created_at DESC) is used."""
        # Create second zone and rack/shelf/bin
        zone_b = Zone.objects.create(
            warehouse=self.warehouse,
            zone_group=self.zone_group,
            zone_name='B4',
            zone_type='GENERAL',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0'),
            width=Decimal('10.0'), height=Decimal('10.0'), depth=Decimal('10.0')
        )
        rack_b = Rack.objects.create(
            zone=zone_b,
            rack_code='RACK-B4-1',
            max_weight=Decimal('500.00'),
            x=Decimal('1.0'), y=Decimal('1.0'), z=Decimal('0.0'),
            width=Decimal('2.0'), height=Decimal('8.0'), depth=Decimal('1.0'),
            rotation_angle=Decimal('0.0')
        )
        shelf_b = Shelf.objects.create(
            rack=rack_b,
            shelf_number=1,
            max_weight=Decimal('100.00'),
            height_from_ground=Decimal('0.5')
        )
        bin_b = Bin.objects.create(
            shelf=shelf_b,
            bin_code='BIN-B4-1-01',
            max_capacity=Decimal('10.00'),
            current_capacity=Decimal('1.00'),
            length=Decimal('50.00'),
            width=Decimal('40.00'),
            height=Decimal('30.00'),
            is_occupied=False
        )

        # Create newer recommendation pointing to zone_b (which is B4)
        StorageRecommendation.objects.create(
            product=self.product,
            zone_group=self.zone_group,
            zone=zone_b,
            recommendation_reason='Optimal zone B4 selected later',
            recommendation_score=0.99,
            recommendation_source=StorageRecommendation.RecommendationSource.RULE_ENGINE,
            recommendation_version='v1'
        )

        url = '/api/recommendations/bin-allocation/'
        response = cast(Response, self.client.post(url, {'product_id': str(self.product.id)}, format='json'))
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert response.data is not None
        data = response.data
        self.assertEqual(data['zone'], 'B4')
        self.assertEqual(data['bin']['code'], 'BIN-B4-1-01')
