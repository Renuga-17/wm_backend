import os
import sys
import django

# Set up Django environment to access settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from integrations.clickhouse_client import ClickHouseClient

def clear_clickhouse():
    print("Connecting to ClickHouse...")
    client_wrapper = ClickHouseClient()
    
    # Check connect
    client = client_wrapper.connect()
    
    print("Fetching all tables in the current ClickHouse database...")
    result = client_wrapper.execute_query("SHOW TABLES")
    
    if result and result.result_rows:
        tables = [row[0] for row in result.result_rows]
        print(f"Found tables: {tables}")
        for table in tables:
            print(f"Dropping ClickHouse table '{table}'...")
            try:
                client_wrapper.execute_query(f"DROP TABLE {table}")
                print(f"Table '{table}' dropped successfully.")
            except Exception as e:
                print(f"Failed to drop table '{table}': {e}")
    else:
        print("No tables found in ClickHouse database.")

if __name__ == '__main__':
    clear_house = clear_clickhouse()
