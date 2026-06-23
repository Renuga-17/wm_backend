import os
import sys
import django
import time

sys.path.append(r"c:\TYN\wm_backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.warehouse.infrastructure.persistence.models import Zone
from apps.warehouse.presentation.api.zone_serializers import ZoneSerializer
from django.db import connection, reset_queries

reset_queries()
t0 = time.time()
zones = Zone.objects.all().order_by('id')
serializer = ZoneSerializer(zones, many=True)
data = serializer.data
t1 = time.time()

print(f"Serialized {len(data)} zones in {t1 - t0:.2f} seconds.")
print(f"Number of SQL queries executed: {len(connection.queries)}")
for q in connection.queries:
    print(f"SQL: {q['sql']}\nTime: {q['time']}\n")
