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

User = get_user_model()
user = User.objects.filter(role='WAREHOUSE_MANAGER').first()

client = APIClient()
client.force_authenticate(user=user)

reset_queries()
t0 = time.time()
response = client.get('/api/inventory/')
t1 = time.time()

print(f"Status: {response.status_code}")
print(f"Time taken: {t1 - t0:.2f} seconds")
print(f"Number of SQL queries: {len(connection.queries)}")
for q in connection.queries:
    print(f"SQL: {q['sql']}\nTime: {q['time']}\n")
