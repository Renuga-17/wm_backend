import os
import sys
import django

# Set up Django environment
sys.path.append("c:\\Users\\vidhyaadaran\\wm_backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def clear_neon_db():
    print("Connecting to Neon PostgreSQL to drop all tables and data...")
    with connection.cursor() as cursor:
        try:
            print("Dropping and recreating public schema...")
            cursor.execute("DROP SCHEMA public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")
            cursor.execute("GRANT ALL ON SCHEMA public TO public;")
            cursor.execute("GRANT ALL ON SCHEMA public TO neondb_owner;")
            print("Successfully cleared all tables and data in Neon DB.")
        except Exception as e:
            print(f"Error during clearing: {e}")
            raise e

if __name__ == '__main__':
    clear_neon_db()
