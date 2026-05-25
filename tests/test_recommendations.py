import pytest
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch
from apps.products.models import Product, ProductCategory
from apps.bins.models import Bin, Shelf
from apps.zones.models import Zone
from apps.warehouses.models import Warehouse, WarehouseLayout, Rack
from apps.users.models import User

@pytest.mark.django_db
class TestWMSAPI:
    def test_login_and_suggest_bin(self, client):
        # Create a user with known credentials for testing
        user = User.objects.create_user(
            username='testuser', 
            password='testpassword',
            email='test@example.com',
            full_name='Test User'
        )
        
        # Test login
        login_url = reverse('token_obtain_pair')
        res = client.post(login_url, {'username': 'testuser', 'password': 'testpassword'}, content_type='application/json')
        assert res.status_code == status.HTTP_200_OK
        access_token = res.data['access']
        
        # Setup mock product & bin
        category = ProductCategory.objects.create(category_name='TestCategory')
        product = Product.objects.create(
            sku='TESTSKU123',
            product_name='Test Product',
            weight=5.50,
            category=category
        )
        
        warehouse = Warehouse.objects.create(name='Test Warehouse')
        layout = WarehouseLayout.objects.create(
            warehouse=warehouse,
            layout_name='Test Layout',
            width=10.0,
            height=10.0,
            depth=10.0
        )
        
        zone = Zone.objects.create(
            warehouse=warehouse,
            zone_name='Zone A',
            zone_type='DRY',
            x=0, y=0, z=0, width=5, height=5, depth=5
        )
        rack = Rack.objects.create(
            zone=zone,
            rack_code='RACK-A1',
            max_weight=1000,
            x=0, y=0, z=0, width=4, height=4, depth=4, rotation_angle=0
        )
        shelf = Shelf.objects.create(
            rack=rack,
            shelf_number=1,
            max_weight=250,
            height_from_ground=0
        )
        bin_obj = Bin.objects.create(
            shelf=shelf,
            bin_code='RACK-A1-L1-B01',
            max_capacity=100,
            is_occupied=False
        )
        
        # Test suggest-bin with authentication header
        suggest_url = '/api/recommendations/suggest-bin/'
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
        
        # Mock the AI Service Client
        with patch('integrations.ai_service_client.AIServiceClient.get_storage_recommendation') as mock_ai:
            mock_ai.return_value = {
                "success": True,
                "recommended_bin_id": str(bin_obj.id),
                "confidence_score": 0.95,
                "reasoning": "High-velocity category co-location."
            }
            
            res = client.post(
                suggest_url,
                {'product_id': str(product.id), 'quantity': 10},
                content_type='application/json',
                **headers
            )
            assert res.status_code == status.HTTP_200_OK
            assert res.data['success'] is True
            assert res.data['recommended_bin_id'] == str(bin_obj.id)
            assert res.data['confidence_score'] == 0.95
            assert res.data['reasoning'] == "High-velocity category co-location."
