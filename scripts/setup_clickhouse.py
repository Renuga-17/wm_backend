import os
import sys
import django

# Set up Django environment to access settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from integrations.clickhouse_client import ClickHouseClient

def setup_schemas():
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "clickhouse_schema.sql")
    print(f"Reading ClickHouse schema definition from {schema_path}...")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        sql_content = f.read()
        
    # Split by semicolon to execute one by one
    statements = sql_content.split(";")
    
    print("Connecting to ClickHouse...")
    client = ClickHouseClient()
    
    for stmt in statements:
        cleaned = stmt.strip()
        # Remove comments and empty lines
        lines = [line.strip() for line in cleaned.split("\n") if line.strip() and not line.strip().startswith("--")]
        if not lines:
            continue
            
        cleaned_stmt = " ".join(lines)
        if not cleaned_stmt:
            continue
            
        # Get table name for logging
        table_name = "unknown"
        if "CREATE TABLE" in cleaned_stmt.upper():
            parts = cleaned_stmt.upper().split("CREATE TABLE")
            if len(parts) > 1:
                table_name = parts[1].split("(")[0].replace("IF NOT EXISTS", "").strip()
                
        print(f"Executing DDL for table '{table_name}'...")
        try:
            client.execute_query(cleaned)
            print(f"Successfully applied DDL for '{table_name}'.")
        except Exception as e:
            print(f"Failed to execute DDL statement for '{table_name}': {e}")
            sys.exit(1)

    print("ClickHouse schema setup completed successfully.")

if __name__ == '__main__':
    setup_schemas()
