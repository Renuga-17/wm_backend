import os, sys, json

# Setup Django environment
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from integrations.clickhouse_client import ClickHouseClient

# Get an active user for authentication
User = get_user_model()
user = User.objects.filter(is_active=True).first()
if not user:
    print('No active user found')
    sys.exit(1)
client = APIClient()
client.force_authenticate(user=user)

# Required ClickHouse tables
tables = [
    'inventory_events',
    'scan_events',
    'sensor_events',
    'warehouse_heatmaps',
    'route_analytics',
    'ai_predictions',
    'demand_forecasts',
]
from django.conf import settings
print("CLICKHOUSE_SETTINGS =", settings.CLICKHOUSE_SETTINGS)
ch = ClickHouseClient()
ch.connect()

report = {}

# Audit tables
for tbl in tables:
    tbl_info = {}
    # Existence & row count
    try:
        count_res = ch.execute_query(f"SELECT count() FROM {tbl}")
        row_count = count_res.result_rows[0][0] if count_res else 0
        tbl_info['exists'] = True
        tbl_info['row_count'] = row_count
    except Exception as e:
        tbl_info['exists'] = False
        tbl_info['row_count'] = 0
        tbl_info['error'] = str(e)
        report[tbl] = tbl_info
        continue
    # Schema
    try:
        desc_res = ch.execute_query(f"DESCRIBE TABLE {tbl}")
        # desc_res.result_rows is list of tuples (name, type, default, ...) – we keep name and type
        schema = [{"name": row[0], "type": row[1]} for row in desc_res.result_rows]
        tbl_info['schema'] = schema
    except Exception as e:
        tbl_info['schema'] = []
        tbl_info['schema_error'] = str(e)
    report[tbl] = tbl_info

# Verify Analytics APIs
api_endpoints = {
    'dashboards': '/api/dashboards/',
    'heatmaps': '/api/dashboards/analytics/heatmaps/',
    'routes': '/api/dashboards/analytics/routes/',
    'telemetry': '/api/dashboards/analytics/telemetry/',
    'throughput': '/api/dashboards/analytics/throughput/',
}
api_report = {}
for name, url in api_endpoints.items():
    resp = client.get(url, {'warehouse_id': '1'})  # use a generic id; adjust if needed
    try:
        data = resp.data if hasattr(resp, 'data') else json.loads(resp.content)
    except Exception:
        data = resp.content.decode() if hasattr(resp, 'content') else str(resp)
    api_report[name] = {
        'status_code': resp.status_code,
        'success': resp.status_code == 200,
        'sample_payload': data if isinstance(data, (dict, list)) else str(data)[:500]
    }

# Output report
final_report = {
    'clickhouse': report,
    'api': api_report,
}
print(json.dumps(final_report, indent=2, default=str))
