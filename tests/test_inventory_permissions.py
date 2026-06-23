import pytest
from rest_framework import status
from django.urls import reverse
from apps.inventory.infrastructure.persistence.models import (
    Inventory, Product, ProductCategory, StockMovement, StorageAllocation
)
from apps.warehouse.infrastructure.persistence.models import Warehouse, Zone, Rack, Shelf, Bin
from apps.identity.infrastructure.persistence.models import User

@pytest.mark.django_db
class TestInventoryPermissionsAPI:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        # Create categories, products, etc.
        self.category = ProductCategory.objects.create(category_name='PermTestCategory')
        self.product = Product.objects.create(
            sku='PERMTESTSKU',
            product_name='Perm Test Product',
            weight=1.50,
            category=self.category
        )
        self.warehouse = Warehouse.objects.create(name='Perm Test Warehouse')
        self.zone = Zone.objects.create(
            warehouse=self.warehouse,
            zone_name='Perm Zone A',
            zone_type='DRY',
            x=0, y=0, z=0, width=5, height=5, depth=5
        )
        self.rack = Rack.objects.create(
            zone=self.zone,
            rack_code='PERM-RACK-A1',
            max_weight=1000,
            x=0, y=0, z=0, width=4, height=4, depth=4, rotation_angle=0
        )
        self.shelf = Shelf.objects.create(
            rack=self.rack,
            shelf_number=1,
            max_weight=250,
            height_from_ground=0
        )
        self.bin = Bin.objects.create(
            shelf=self.shelf,
            bin_code='PERM-RACK-A1-L1-B01',
            max_capacity=100,
            is_occupied=False
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            total_quantity=10,
            reserved_quantity=0,
            damaged_quantity=0
        )
        self.movement = StockMovement.objects.create(
            product=self.product,
            from_bin=self.bin,
            to_bin=self.bin,
            quantity=5,
            movement_type='PUTAWAY_COMPLETED'
        )
        self.allocation = StorageAllocation.objects.create(
            product=self.product,
            bin=self.bin,
            quantity=5
        )

    def test_inventory_read_public(self, client):
        # GET /api/inventory/ should be 200 without token
        url = '/api/inventory/'
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
        assert any(r['sku'] == 'PERMTESTSKU' for r in results)

    def test_inventory_write_protected(self, client):
        # POST /api/inventory/ should fail with 401/403 without token
        url = '/api/inventory/'
        response = client.post(url, {'product': str(self.product.id), 'total_quantity': 5}, content_type='application/json')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_products_read_public(self, client):
        # GET /api/products/ should be 200 without token
        url = '/api/products/'
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
        assert any(p['sku'] == 'PERMTESTSKU' for p in results)

    def test_products_write_protected(self, client):
        # POST /api/products/ should fail with 401/403 without token
        url = '/api/products/'
        response = client.post(url, {'sku': 'NEWPRODUCTSKU', 'product_name': 'New Product'}, content_type='application/json')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_movements_read_public(self, client):
        # GET /api/movements/ should be 200 without token
        url = '/api/movements/'
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1

    def test_movements_write_protected(self, client):
        # POST /api/movements/ should fail with 401/403 without token
        url = '/api/movements/'
        response = client.post(url, {'product': str(self.product.id), 'quantity': 1}, content_type='application/json')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_allocations_read_public(self, client):
        # GET /api/movements/allocations/ should be 200 without token
        url = '/api/movements/allocations/'
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1

    def test_allocations_write_protected(self, client):
        # POST /api/movements/allocations/ should fail with 401/403 without token
        url = '/api/movements/allocations/'
        response = client.post(url, {'product': str(self.product.id), 'bin': str(self.bin.id), 'quantity': 1}, content_type='application/json')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
