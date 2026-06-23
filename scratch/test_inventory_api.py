import os
import sys
import django
import time

sys.path.append(r"c:\TYN\wm_backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.inventory.infrastructure.persistence.models import Inventory
from apps.inventory.presentation.api.inventory_serializers import InventorySerializer
from django.db import connection, reset_queries

reset_queries()
t0 = time.time()
inventory = Inventory.objects.all().select_related(
    'product',
    'product__category'
).prefetch_related(
    'product__dimensions',
    'product__allocations',
    'product__allocations__bin',
    'product__allocations__bin__shelf',
    'product__allocations__bin__shelf__rack',
    'product__allocations__bin__shelf__rack__zone',
    'product__allocations__bin__shelf__rack__zone__warehouse'
)
# Force queryset evaluation
count = inventory.count()
print(f"Total inventory records: {count}")

t0_serialize = time.time()
serializer = InventorySerializer(inventory[:50], many=True) # Let's test first 50 to see
data = serializer.data
t1 = time.time()

print(f"Serialized 50 items in {t1 - t0_serialize:.2f} seconds.")
print(f"Total time (including count): {t1 - t0:.2f} seconds.")
print(f"Number of SQL queries executed: {len(connection.queries)}")
for q in connection.queries:
    print(f"SQL: {q['sql']}\nTime: {q['time']}\n")
