import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wm_backend.settings')
django.setup()

from rest_framework.test import APIClient
from django.urls import reverse

client = APIClient()

# Create test user
from apps.identity.infrastructure.persistence.models import User
User.objects.filter(username='verify_user').delete()
user = User.objects.create_user(username='verify_user', password='verify_pass', email='verify@example.com')

# Obtain JWT token
login_url = reverse('token_obtain_pair')
login_resp = client.post(login_url, {'username': 'verify_user', 'password': 'verify_pass'}, format='json')
if login_resp.status_code != 200:
    print('Login failed', login_resp.status_code, login_resp.content)
    exit(1)
access_token = login_resp.data['access']
client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

endpoints = [
    {'method': 'get', 'url': '/api/recommendations/', 'desc': 'List recommendations'},
    {'method': 'post', 'url': '/api/recommendations/suggest-bin/', 'desc': 'Suggest bin', 'payload': {}},
    {'method': 'post', 'url': '/api/recommendations/allocate/', 'desc': 'Allocate', 'payload': {}},
    {'method': 'post', 'url': '/api/ai/predict-demand/', 'desc': 'Predict demand', 'payload': {}},
    {'method': 'post', 'url': '/api/ai/optimize-slotting/', 'desc': 'Optimize slotting', 'payload': {}},
    {'method': 'get', 'url': '/api/ai/congestion-risk/', 'desc': 'Congestion risk', 'params': {}},
    {'method': 'get', 'url': '/api/ai/recommendations/', 'desc': 'AI recommendations', 'params': {}},
    {'method': 'get', 'url': '/api/ai/slotting-score/', 'desc': 'Slotting score', 'params': {}},
    {'method': 'get', 'url': '/api/ai/hotspot-prevention/', 'desc': 'Hotspot prevention', 'params': {}},
    {'method': 'get', 'url': '/api/ai/operational-scores/', 'desc': 'Operational scores', 'params': {}},
    {'method': 'get', 'url': '/api/ai/alerts/', 'desc': 'Alerts list', 'params': {}},
    {'method': 'post', 'url': '/api/ai/alerts/', 'desc': 'Resolve alert', 'payload': {}},
    {'method': 'post', 'url': '/api/ai/feedback/', 'desc': 'Feedback', 'payload': {}},
]

results = []
for ep in endpoints:
    method = ep['method']
    url = ep['url']
    try:
        if method == 'get':
            resp = client.get(url, data=ep.get('params', {}), format='json')
        else:
            resp = client.post(url, data=ep.get('payload', {}), format='json')
        results.append({
            'url': url,
            'method': method.upper(),
            'status': resp.status_code,
            'response': resp.data if hasattr(resp, 'data') else resp.content.decode()
        })
    except Exception as e:
        results.append({
            'url': url,
            'method': method.upper(),
            'status': 'Error',
            'response': str(e)
        })

print(json.dumps(results, indent=2))
