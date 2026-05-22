import os
import sys
import django

# Set up Django environment to access settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from integrations.clickhouse_client import ClickHouseClient

def setup_schemas():
    print("Connecting to ClickHouse...")
    client = ClickHouseClient()
    
    # Define DDL queries
    queries = [
        """
        CREATE TABLE IF NOT EXISTS warehouse_events (
            event_id UUID,
            event_type String,
            severity String,
            timestamp DateTime64(3),
            warehouse_id UUID,
            zone_id Nullable(UUID),
            rack_id Nullable(UUID),
            bin_id Nullable(UUID),
            product_id Nullable(UUID),
            quantity Nullable(Int32),
            user_id Nullable(UUID),
            duration_ms Nullable(UInt32),
            status String,
            metadata Map(String, String)
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (warehouse_id, event_type, timestamp)
        TTL timestamp + INTERVAL 2 YEAR;
        """,
        """
        CREATE TABLE IF NOT EXISTS sensor_telemetry (
            timestamp DateTime64(3),
            sensor_id String,
            sensor_type String,
            warehouse_id UUID,
            zone_id UUID,
            value Float64,
            metadata Map(String, String)
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (warehouse_id, zone_id, sensor_type, timestamp)
        TTL timestamp + INTERVAL 2 YEAR;
        """,
        """
        CREATE TABLE IF NOT EXISTS utilization_snapshots (
            timestamp DateTime,
            warehouse_id UUID,
            zone_id UUID,
            total_bins UInt32,
            occupied_bins UInt32,
            utilization_rate Float64,
            total_volume_m3 Float64,
            used_volume_m3 Float64
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (warehouse_id, zone_id, timestamp)
        TTL timestamp + INTERVAL 5 YEAR;
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_recommendation_events (
            recommendation_id UUID,
            timestamp DateTime64(3),
            product_id UUID,
            requested_quantity UInt32,
            model_version String,
            recommended_bin_id UUID,
            confidence_score Float64,
            reasoning String,
            is_accepted UInt8,
            override_bin_id Nullable(UUID),
            response_time_ms UInt32,
            metadata Map(String, String)
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (product_id, model_version, timestamp)
        TTL timestamp + INTERVAL 2 YEAR;
        """,
        """
        CREATE TABLE IF NOT EXISTS sku_velocity_analytics (
            date Date,
            product_id UUID,
            sku String,
            category_name String,
            total_picks UInt32,
            total_picked_quantity UInt32,
            total_putaways UInt32,
            total_putaway_quantity UInt32,
            inventory_turnover_rate Float64,
            velocity_class String
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (product_id, date)
        TTL date + INTERVAL 3 YEAR;
        """
    ]
    
    for query in queries:
        # Extract table name for print logging
        table_name = query.split("TABLE IF NOT EXISTS")[1].split("(")[0].strip()
        print(f"Creating ClickHouse table '{table_name}'...")
        try:
            client.execute_query(query)
            print(f"Table '{table_name}' creation query sent successfully.")
        except Exception as e:
            print(f"Failed to create table '{table_name}': {e}")
            sys.exit(1)

    print("ClickHouse schema setup completed successfully.")

if __name__ == '__main__':
    setup_schemas()
