import os, sys, json
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
    print('No active user')
    sys.exit(1)
client = APIClient()
client.force_authenticate(user=user)
layout_id = 'd6e218b6-8f18-4154-8574-f7b64e581f53'
endpoints = [
    ('layout', f'/api/twin/layout/{layout_id}/'),
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
        data = json.dumps(resp.data)
    except Exception:
        data = resp.content.decode()
    print(data[:500])
