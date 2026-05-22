import os
import sys
import django

# Set up Django environment
sys.path.append("c:\\Users\\vidhyaadaran\\wm_backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def setup_neon_schema():
    schema_path = "c:\\Users\\vidhyaadaran\\wm_backend\\docs\\neon_schema.sql"
    print(f"Reading schema definition from {schema_path}...")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print("Connecting to Neon PostgreSQL and executing DDL statements...")
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql_content)
            print("DDL schema execution completed successfully.")
        except Exception as e:
            print(f"Error during schema execution: {e}")
            raise e

if __name__ == '__main__':
    setup_neon_schema()
