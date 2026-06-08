import os, sys, json

# Setup Django environment
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

# Print runtime ClickHouse settings
from django.conf import settings
print('CLICKHOUSE_SETTINGS =', settings.CLICKHOUSE_SETTINGS)

# Connect using ClickHouseClient
from integrations.clickhouse_client import ClickHouseClient
ch = ClickHouseClient()
client = ch.connect()

def run_query(query):
    try:
        result = ch.execute_query(query)
        # result.result_rows may be None if no rows
        rows = result.result_rows if result else []
        return rows
    except Exception as e:
        return f'Error: {e}'

# 1. SELECT 1
print('SELECT 1 =>', run_query('SELECT 1'))
# 2. SHOW DATABASES
print('SHOW DATABASES =>', run_query('SHOW DATABASES'))
# 3. SHOW TABLES
print('SHOW TABLES =>', run_query('SHOW TABLES'))
