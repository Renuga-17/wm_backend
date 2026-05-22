import os
import sys
import django
import random
from datetime import datetime, timedelta

# Set up Django environment
sys.path.append("c:\\Users\\vidhyaadaran\\wm_backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from integrations.clickhouse_client import ClickHouseClient

def get_warehouse_structure():
    print("Fetching warehouse structural data from PostgreSQL...")
    zones = []
    bin_counts = {}
    
    with connection.cursor() as cursor:
        # Get all zones
        cursor.execute("SELECT id, warehouse_id, zone_name, zone_type FROM zones;")
        zones = cursor.fetchall()
        
        # Get count of bins grouped by zone_id
        cursor.execute("""
            SELECT z.id, COUNT(b.id) 
            FROM bins b
            JOIN shelves s ON b.shelf_id = s.id
            JOIN racks r ON s.rack_id = r.id
            JOIN zones z ON r.zone_id = z.id
            GROUP BY z.id;
        """)
        counts = cursor.fetchall()
        for zid, count in counts:
            bin_counts[str(zid)] = count
            
    print(f"Retrieved {len(zones)} zones from PostgreSQL.")
    return zones, bin_counts

def seed_telemetry():
    zones, bin_counts = get_warehouse_structure()
    ch_client = ClickHouseClient()
    client = ch_client.connect()

    sensor_data = []
    util_data = []
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=30)
    
    current_time = start_time
    total_hours = 30 * 24
    
    print(f"Generating telemetry data for {total_hours} hours...")
    
    while current_time <= end_time:
        for zone in zones:
            zone_id, wh_id, name, ztype = zone
            zone_str = str(zone_id)
            wh_str = str(wh_id)
            
            # Determine hourly fluctuations
            hour = current_time.hour
            is_peak = 8 <= hour <= 18
            
            # 1. Temperature Telemetry
            if ztype == 'COLD':
                temp = round(random.uniform(1.5, 4.8), 2)
                humidity = round(random.uniform(75.0, 85.0), 2)
            elif ztype == 'HAZARDOUS':
                temp = round(random.uniform(14.0, 18.0), 2)
                humidity = round(random.uniform(35.0, 45.0), 2)
            else:  # DRY
                temp = round(random.uniform(19.0, 23.5), 2)
                humidity = round(random.uniform(45.0, 55.0), 2)
                
            # Traffic Density and Speed
            traffic = round(random.uniform(40.0, 95.0), 2) if is_peak else round(random.uniform(5.0, 30.0), 2)
            speed = round(random.uniform(1.2, 3.5), 2) if is_peak else round(random.uniform(3.0, 5.0), 2) # Faster when empty
            
            # Append Sensor records
            sensor_data.append([current_time, f"temp-{name}", "TEMPERATURE", wh_str, zone_str, temp, {}])
            sensor_data.append([current_time, f"humid-{name}", "HUMIDITY", wh_str, zone_str, humidity, {}])
            sensor_data.append([current_time, f"traffic-{name}", "TRAFFIC_DENSITY", wh_str, zone_str, traffic, {}])
            sensor_data.append([current_time, f"speed-{name}", "SPEED", wh_str, zone_str, speed, {}])
            
            # 2. Utilization snapshots
            total_b = bin_counts.get(zone_str, 50)  # Default to 50 if zero bins found
            occupancy_rate = random.uniform(0.70, 0.92) if is_peak else random.uniform(0.65, 0.88)
            occupied_b = int(total_b * occupancy_rate)
            
            total_vol = total_b * 1.2  # avg bin volume 1.2 m3
            used_vol = occupied_b * round(random.uniform(0.7, 1.1), 2)
            
            util_data.append([
                current_time,
                wh_str,
                zone_str,
                total_b,
                occupied_b,
                round(occupancy_rate, 4),
                total_vol,
                round(used_vol, 2)
            ])
            
        current_time += timedelta(hours=1)

    # Ingest Sensor Telemetry
    print(f"Generated {len(sensor_data)} sensor records. Ingesting to ClickHouse...")
    sensor_cols = ['timestamp', 'sensor_id', 'sensor_type', 'warehouse_id', 'zone_id', 'value', 'metadata']
    batch_size = 5000
    for i in range(0, len(sensor_data), batch_size):
        batch = sensor_data[i:i+batch_size]
        client.insert('sensor_telemetry', batch, column_names=sensor_cols)
        print(f" - Ingested sensor batch {i // batch_size + 1}/{(len(sensor_data) - 1) // batch_size + 1}")
        
    # Ingest Utilization Snapshots
    print(f"Generated {len(util_data)} utilization snapshot records. Ingesting to ClickHouse...")
    util_cols = [
        'timestamp', 'warehouse_id', 'zone_id', 'total_bins', 
        'occupied_bins', 'utilization_rate', 'total_volume_m3', 'used_volume_m3'
    ]
    for i in range(0, len(util_data), batch_size):
        batch = util_data[i:i+batch_size]
        client.insert('utilization_snapshots', batch, column_names=util_cols)
        print(f" - Ingested utilization batch {i // batch_size + 1}/{(len(util_data) - 1) // batch_size + 1}")

    print("ClickHouse telemetry seeding completed successfully!")

if __name__ == '__main__':
    seed_telemetry()
