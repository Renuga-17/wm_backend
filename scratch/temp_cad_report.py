import os, sys, django
# Ensure project root is on PYTHONPATH
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wm_backend.settings')

django.setup()

from apps.warehouse.infrastructure.persistence.models import WarehouseLayout, CADObject
from django.db.models import Count

print('WarehouseLayout count:', WarehouseLayout.objects.count())
print('CADObject count:', CADObject.objects.count())

print('Sample CADObjects (up to 10):')
for obj in CADObject.objects.values('object_type','detected_label','x','y','z','width','height','depth')[:10]:
    print(dict(obj))

print('CADObjects grouped by detected_label:')
for g in CADObject.objects.values('detected_label').annotate(cnt=Count('id')).order_by('-cnt'):
    print(f"{g['detected_label']} = {g['cnt']}")
