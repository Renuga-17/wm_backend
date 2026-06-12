from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from apps.inventory.infrastructure.persistence.models import Product, ProductCategory
from apps.recommendations.models.product_classification import ProductClassification
from apps.recommendations.models.recommendation_rule import RecommendationRule

User = get_user_model()

class ProductClassificationAPITestCase(TestCase):
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
        
        self.product_unclassified = Product.objects.create(
            category=self.category,
            sku='SKU-PHONE-01',
            product_name='Smartphone',
            weight=Decimal('0.50'),
            is_fragile=False,
            is_hazardous=False
        )

        self.classification = ProductClassification.objects.create(
            product=self.product,
            movement_type=RecommendationRule.MovementType.FAST,
            storage_type=RecommendationRule.StorageType.GENERAL
        )

        self.list_url = '/api/product-classifications/'
        self.detail_url = f'/api/product-classifications/{self.classification.id}/'

    def test_list_classifications(self):
        """Test GET list of classifications."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(str(response.data['results'][0]['product']), str(self.product.id))

    def test_retrieve_classification(self):
        """Test GET single classification."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['product']), str(self.product.id))
        self.assertEqual(response.data['movement_type'], 'FAST')
        self.assertEqual(response.data['storage_type'], 'GENERAL')

    def test_create_classification_success(self):
        """Test POST create classification."""
        payload = {
            'product': str(self.product_unclassified.id),
            'movement_type': 'SLOW',
            'storage_type': 'SECURE'
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductClassification.objects.count(), 2)
        
        new_classification = ProductClassification.objects.get(product=self.product_unclassified)
        self.assertEqual(new_classification.movement_type, 'SLOW')
        self.assertEqual(new_classification.storage_type, 'SECURE')

    def test_create_classification_invalid_choices(self):
        """Test POST create classification with invalid movement_type or storage_type choice."""
        # Invalid movement type
        payload = {
            'product': str(self.product_unclassified.id),
            'movement_type': 'INVALID_TYPE',
            'storage_type': 'GENERAL'
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('movement_type', response.data)

        # Invalid storage type
        payload = {
            'product': str(self.product_unclassified.id),
            'movement_type': 'SLOW',
            'storage_type': 'INVALID_STORAGE'
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('storage_type', response.data)

    def test_create_duplicate_classification_fails(self):
        """Test POST creating another classification for an already classified product fails."""
        payload = {
            'product': str(self.product.id),
            'movement_type': 'SLOW',
            'storage_type': 'GENERAL'
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product', response.data)

    def test_update_classification(self):
        """Test PUT/PATCH update classification."""
        # Partial update
        payload = {
            'movement_type': 'SLOW'
        }
        response = self.client.patch(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.classification.refresh_from_db()
        self.assertEqual(self.classification.movement_type, 'SLOW')

        # Full update
        payload = {
            'product': str(self.product.id),
            'movement_type': 'HAZARDOUS',
            'storage_type': 'COLD'
        }
        response = self.client.put(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.classification.refresh_from_db()
        self.assertEqual(self.classification.movement_type, 'HAZARDOUS')
        self.assertEqual(self.classification.storage_type, 'COLD')

    def test_delete_classification(self):
        """Test DELETE classification."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProductClassification.objects.count(), 0)
