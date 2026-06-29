from typing import cast
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.response import Response
from django.conf import settings
from decimal import Decimal

from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory
from apps.recommendations.models.recommendation_rule import RecommendationRule
from apps.recommendations.models.product_classification import ProductClassification
from apps.recommendations.models.storage_recommendation import StorageRecommendation
from apps.recommendations.services.zone_group_selection_service import ZoneGroupSelectionService
from apps.recommendations.services.zone_selection_service import ZoneSelectionService
from apps.recommendations.services.ml_recommendation_service import MLRecommendationService
from apps.recommendations.services.recommendation_orchestrator import RecommendationOrchestrator
from apps.recommendations.services.storage_recommendation_service import StorageRecommendationService

User = get_user_model()

class StorageRecommendationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(  # type: ignore
            username='test_user',
            password='test_password',
            email='test@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        # Create base test data
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            location='Test Location',
            total_area_sqft=Decimal('10000.00')
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
            x=Decimal('0.0'),
            y=Decimal('0.0'),
            z=Decimal('0.0'),
            width=Decimal('10.0'),
            height=Decimal('10.0'),
            depth=Decimal('10.0')
        )

        self.rack = Rack.objects.create(
            zone=self.zone,
            rack_code='RACK-A2-1',
            max_weight=Decimal('5000.00'),
            x=Decimal('1.0'),
            y=Decimal('1.0'),
            z=Decimal('0.0'),
            width=Decimal('2.0'),
            height=Decimal('8.0'),
            depth=Decimal('1.0'),
            rotation_angle=Decimal('0.0')
        )

        self.shelf = Shelf.objects.create(
            rack=self.rack,
            shelf_number=1,
            max_weight=Decimal('1000.00'),
            height_from_ground=Decimal('0.5')
        )

        self.bin = Bin.objects.create(
            shelf=self.shelf,
            bin_code='BIN-A2-1-01',
            max_capacity=Decimal('100.00'),
            current_capacity=Decimal('20.00'),  # 80% free capacity
            is_occupied=False
        )

        self.category = ProductCategory.objects.create(
            category_name='Electronics'
        )

        self.product = Product.objects.create(
            category=self.category,
            sku='SKU-PROD-999',
            product_name='Super Test Widget',
            weight=Decimal('5.5'),
            is_fragile=False,
            is_hazardous=False
        )

        # Create Product Classification
        self.classification = ProductClassification.objects.create(
            product=self.product,
            movement_type='FAST',
            storage_type='GENERAL'
        )

        # Create Recommendation Rule
        self.rule = RecommendationRule.objects.create(
            movement_type='FAST',
            storage_type='GENERAL',
            zone_group_type='GENERAL_STORAGE',
            priority=10,
            description='Test general fast storage rule'
        )

    def test_recommendation_rule_creation(self):
        self.assertEqual(RecommendationRule.objects.count(), 1)
        self.assertEqual(self.rule.zone_group_type, 'GENERAL_STORAGE')
        self.assertEqual(str(self.rule), f"Rule {self.rule.id}: FAST/GENERAL → GENERAL_STORAGE")  # type: ignore

    def test_product_classification_creation(self):
        self.assertEqual(ProductClassification.objects.count(), 1)
        self.assertEqual(self.classification.movement_type, 'FAST')
        self.assertEqual(str(self.classification), f"Classification for SKU-PROD-999: FAST/GENERAL")

    def test_zone_group_selection_service(self):
        service = ZoneGroupSelectionService()
        selected_zg = service.select(movement_type='FAST', storage_type='GENERAL')
        self.assertEqual(selected_zg, self.zone_group)

    def test_zone_group_selection_service_no_suitable(self):
        service = ZoneGroupSelectionService()
        with self.assertRaises(ValueError):
            service.select(movement_type='HAZARDOUS', storage_type='COLD')

    def test_zone_selection_service_capacity_calculation(self):
        service = ZoneSelectionService()
        metrics = service.calculate_zone_capacity_metrics(self.zone)
        self.assertEqual(metrics['total_capacity'], 100.0)
        self.assertEqual(metrics['used_capacity'], 20.0)
        self.assertEqual(metrics['available_capacity'], 80.0)
        self.assertEqual(metrics['available_capacity_percentage'], 80.0)
        self.assertEqual(metrics['current_utilization_percentage'], 20.0)

    def test_zone_selection_service_scoring(self):
        service = ZoneSelectionService()
        # Test score combinations
        score = service.calculate_recommendation_score(
            capacity_pct=80.0,
            utilization_pct=20.0,
            priority=0.8,
            active=True
        )
        # Capacity Score = 80/100 * 0.40 = 0.32
        # Utilization Score = (100-20)/100 * 0.30 = 0.24
        # Priority Score = 0.8 * 0.20 = 0.16
        # Zone Status Score = 1.0 * 0.10 = 0.10
        # Expected: 0.32 + 0.24 + 0.16 + 0.10 = 0.82
        self.assertAlmostEqual(score, 0.82)

    def test_zone_selection_service_reject_capacity(self):
        # Update bin to exceed min capacity (make it 95% utilized -> 5% free capacity)
        self.bin.current_capacity = Decimal('95.00')
        self.bin.save()

        service = ZoneSelectionService()
        with self.assertRaises(ValueError):
            # Should raise ValueError because free capacity is 5% which is below WAREHOUSE_MIN_FREE_CAPACITY (10%)
            service.select_best_zone(self.zone_group)

    def test_recommendation_orchestrator_rule_engine(self):
        orchestrator = RecommendationOrchestrator()
        rec_data = orchestrator.get_recommendation(self.product)
        self.assertEqual(rec_data['zone_group'], self.zone_group)
        self.assertEqual(rec_data['zone'], self.zone)
        self.assertEqual(rec_data['recommendation_source'], 'RULE_ENGINE')
        self.assertTrue(rec_data['recommendation_score'] > 0.0)

    def test_recommendation_orchestrator_ml_fallback(self):
        # Temporarily enable ML without proper path config -> should fallback to rule engine
        settings.WAREHOUSE_RECOMMENDATION_USE_ML = True
        settings.ML_MODEL_PATH = '/invalid/model/path.pkl'
        
        orchestrator = RecommendationOrchestrator()
        rec_data = orchestrator.get_recommendation(self.product)
        self.assertEqual(rec_data['recommendation_source'], 'RULE_ENGINE')

        # Cleanup settings
        settings.WAREHOUSE_RECOMMENDATION_USE_ML = False
        settings.ML_MODEL_PATH = ''

    def test_storage_recommendation_service_generate(self):
        service = StorageRecommendationService()
        rec = service.generate_recommendation(self.product.id)
        self.assertEqual(rec.product, self.product)
        self.assertEqual(rec.zone_group, self.zone_group)
        self.assertEqual(rec.zone, self.zone)
        self.assertEqual(rec.recommendation_source, 'RULE_ENGINE')
        self.assertEqual(StorageRecommendation.objects.count(), 1)

    def test_api_recommendation_success(self):
        response = cast(Response, self.client.post(
            '/api/recommendations/storage/',
            {'product_id': str(self.product.id)},
            format='json'
        ))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert response.data is not None
        self.assertEqual(response.data['zone_group'], 'A')
        self.assertEqual(response.data['zone'], 'A2')
        self.assertEqual(response.data['recommendation_source'], 'RULE_ENGINE')
        self.assertTrue(response.data['recommendation_score'] > 0.0)

    def test_api_recommendation_invalid_product(self):
        response = cast(Response, self.client.post(
            '/api/recommendations/storage/',
            {'product_id': '00000000-0000-0000-0000-000000000000'},
            format='json'
        ))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_recommendation_missing_classification(self):
        # Create product without classification
        other_product = Product.objects.create(
            category=self.category,
            sku='SKU-PROD-888',
            product_name='Super Test Widget 2',
            weight=Decimal('10.0'),
            is_fragile=False,
            is_hazardous=False
        )
        response = cast(Response, self.client.post(
            '/api/recommendations/storage/',
            {'product_id': str(other_product.id)},
            format='json'
        ))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
