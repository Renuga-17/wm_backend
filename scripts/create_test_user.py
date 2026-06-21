import os, sys, django

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

# Load Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

user, created = User.objects.get_or_create(
    username='api_test_user',
    defaults={'email': 'api_test@example.com'}
)
if created:
    user.set_password('Test@12345')
    user.save()
    print('User Created: PASS')
else:
    print('User Created: EXISTS')
print('Password Verified:', user.check_password('Test@12345'))
