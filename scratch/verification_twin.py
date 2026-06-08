import os, sys, json
# Ensure project root is on PYTHONPATH
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.filter(is_active=True).first()
if not user:
    print('No active user found')
    sys.exit(1)
client = APIClient()
client.force_authenticate(user=user)
from apps.warehouse.infrastructure.persistence.models import WarehouseLayout
layout = WarehouseLayout.objects.first()
if not layout:
    print('No WarehouseLayout found')
    sys.exit(1)
endpoints = [
    ('layout', f'/api/twin/layout/{layout.id}/'),
    ('racks', '/api/twin/racks'),
    ('zones', '/api/twin/zones'),
    ('occupancy', '/api/twin/occupancy'),
    ('paths', '/api/twin/paths'),
    ('summary', '/api/twin/summary'),
]
for name, url in endpoints:
    resp = client.get(url)
    print(name, resp.status_code)
    try:
        # DRF Response objects have .data
        data = json.dumps(resp.data)
    except AttributeError:
        # Fallback to raw content (bytes) and decode
        content = resp.content if hasattr(resp, 'content') else str(resp)
        try:
            data = json.dumps(json.loads(content))
        except Exception:
            data = str(content)
    print(data[:500])
