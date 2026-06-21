import os, django, json, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wm_backend.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
print('Users in DB:')
print(list(User.objects.values('username','is_active','is_staff','is_superuser'))

import requests
BASE_URL = 'http://127.0.0.1:8000/api/users/login/'
payload = {'username':'admin','password':'admin'}
resp = requests.post(BASE_URL, json=payload)
print('\nLogin attempt response:')
print('Status:', resp.status_code)
try:
    print('JSON:', resp.json())
except Exception:
    print('Text:', resp.text)
