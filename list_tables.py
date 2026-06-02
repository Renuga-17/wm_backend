import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection
print('\n'.join(connection.introspection.table_names()))
