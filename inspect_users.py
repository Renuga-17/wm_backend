import os, sys, json

# Add project root to sys.path so that 'wm_backend' package can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wm_backend.config.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

users = []
for u in User.objects.all():
    users.append({
        'id': str(u.id),
        'username': u.username,
        'is_active': u.is_active,
        'role': getattr(u, 'role', None),
    })

print(json.dumps(users, indent=2))
