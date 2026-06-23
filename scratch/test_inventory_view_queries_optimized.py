import os
import sys
import django
import time

sys.path.append(r"c:\TYN\wm_backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection, reset_queries
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from apps.inventory.infrastructure.persistence.models import StorageAllocation, Inventory
from apps.inventory.presentation.api.inventory_serializers import InventorySerializer

User = get_user_model()
user = User.objects.filter(role='WAREHOUSE_MANAGER').first()

# Build client
client = APIClient()
client.force_authenticate(user=user)

# Patch InventoryViewSet or query manually to verify
from apps.inventory.presentation.api.inventory_views import InventoryViewSet
original_get_queryset = InventoryViewSet.get_queryset

def new_get_queryset(self):
    return Inventory.objects.all().select_related(
        'product',
        'product__category'
    ).prefetch_related(
        'product__dimensions',
        Prefetch(
            'product__allocations',
            queryset=StorageAllocation.objects.all().select_related(
                'bin',
                'bin__shelf',
                'bin__shelf__rack',
                'bin__shelf__rack__zone',
                'bin__shelf__rack__zone__warehouse'
            )
        )
    )

InventoryViewSet.get_queryset = new_get_queryset

reset_queries()
t0 = time.time()
response = client.get('/api/inventory/')
t1 = time.time()

print(f"Status: {response.status_code}")
print(f"Time taken: {t1 - t0:.2f} seconds")
print(f"Number of SQL queries: {len(connection.queries)}")
for q in connection.queries:
    print(f"SQL: {q['sql']}\nTime: {q['time']}\n")
