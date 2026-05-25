import os
import sys
import django
from datetime import datetime

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from integrations.clickhouse_client import ClickHouseClient

def load_spatial_lookup():
    print("Loading bin spatial lookup mapping from PostgreSQL...")
    lookup = {}
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                b.bin_id AS bin_id,
                r.rack_id AS rack_id,
                z.zone_id AS zone_id,
                z.warehouse_id AS warehouse_id
            FROM bins b
            JOIN shelves s ON b.shelf_id = s.shelf_id
            JOIN racks r ON s.rack_id = r.rack_id
            JOIN zones z ON r.zone_id = z.zone_id
        """)
        rows = cursor.fetchall()
        for row in rows:
            lookup[str(row[0])] = {
                'rack_id': str(row[1]) if row[1] else None,
                'zone_id': str(row[2]) if row[2] else None,
                'warehouse_id': str(row[3]) if row[3] else None
            }
    print(f"Loaded spatial lookup mapping for {len(lookup)} bins.")
    return lookup


def ingest_data():
    spatial_lookup = load_spatial_lookup()
    ch_client = ClickHouseClient()
    client = ch_client.connect()

    events = []
    
    # 1. Fetch Putaway Tasks
    print("Extracting Putaway Tasks...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, product_id, assigned_bin_id, assigned_to, status, 
                   created_at, completed_at, route_json
            FROM putaway_tasks;
        """)
        putaway_rows = cursor.fetchall()
        for row in putaway_rows:
            p_id, prod_id, bin_id, user_id, status, created_at, completed_at, route_json = row
            bin_str = str(bin_id) if bin_id else None
            spatial = spatial_lookup.get(bin_str, {'rack_id': None, 'zone_id': None, 'warehouse_id': None})
            
            # Map duration if completed
            duration_ms = None
            if created_at and completed_at:
                duration_ms = int((completed_at - created_at).total_seconds() * 1000)
            
            # Map completed/assigned status
            event_type = 'PUTAWAY_CONFIRMED' if status == 'COMPLETED' else 'PUTAWAY_ASSIGNED'
            timestamp = completed_at if completed_at else created_at
            
            metadata = {}
            if route_json:
                metadata['route'] = str(route_json)

            events.append([
                str(p_id),
                event_type,
                'INFO',
                timestamp,
                spatial['warehouse_id'],
                spatial['zone_id'],
                spatial['rack_id'],
                bin_str,
                str(prod_id) if prod_id else None,
                None,  # Putaway items reference inbound order quantity
                str(user_id) if user_id else None,
                duration_ms,
                status,
                metadata
            ])

    # 2. Fetch Pick Tasks
    print("Extracting Pick Tasks...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, product_id, bin_id, assigned_to, quantity, status, 
                   created_at, completed_at
            FROM pick_tasks;
        """)
        pick_rows = cursor.fetchall()
        for row in pick_rows:
            p_id, prod_id, bin_id, user_id, qty, status, created_at, completed_at = row
            bin_str = str(bin_id) if bin_id else None
            spatial = spatial_lookup.get(bin_str, {'rack_id': None, 'zone_id': None, 'warehouse_id': None})
            
            duration_ms = None
            if created_at and completed_at:
                duration_ms = int((completed_at - created_at).total_seconds() * 1000)
            
            event_type = 'PICK_CONFIRMED' if status == 'COMPLETED' else 'PICK_ASSIGNED'
            timestamp = completed_at if completed_at else created_at
            
            events.append([
                str(p_id),
                event_type,
                'INFO',
                timestamp,
                spatial['warehouse_id'],
                spatial['zone_id'],
                spatial['rack_id'],
                bin_str,
                str(prod_id) if prod_id else None,
                qty,
                str(user_id) if user_id else None,
                duration_ms,
                status,
                {}
            ])

    # 3. Fetch Stock Movements
    print("Extracting Stock Movements...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, product_id, from_bin_id, to_bin_id, movement_type, 
                   quantity, moved_by, moved_at
            FROM stock_movements;
        """)
        movement_rows = cursor.fetchall()
        for row in movement_rows:
            m_id, prod_id, from_bin, to_bin, move_type, qty, user_id, moved_at = row
            bin_str = str(to_bin) if to_bin else (str(from_bin) if from_bin else None)
            spatial = spatial_lookup.get(bin_str, {'rack_id': None, 'zone_id': None, 'warehouse_id': None})
            
            metadata = {
                'movement_type': str(move_type),
                'from_bin_id': str(from_bin) if from_bin else '',
                'to_bin_id': str(to_bin) if to_bin else ''
            }
            
            events.append([
                str(m_id),
                'STOCK_MOVEMENT',
                'INFO',
                moved_at,
                spatial['warehouse_id'],
                spatial['zone_id'],
                spatial['rack_id'],
                bin_str,
                str(prod_id) if prod_id else None,
                qty,
                str(user_id) if user_id else None,
                None,
                'SUCCESS',
                metadata
            ])

    # Batch Insert into ClickHouse
    print(f"Total events compiled: {len(events)}. Ingesting to ClickHouse...")
    
    column_names = [
        'event_id', 'event_type', 'severity', 'timestamp', 'warehouse_id', 
        'zone_id', 'rack_id', 'bin_id', 'product_id', 'quantity', 
        'user_id', 'duration_ms', 'status', 'metadata'
    ]
    
    # Batch slice of 2000 events to prevent payload overload
    batch_size = 2000
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        client.insert('warehouse_events', batch, column_names=column_names)
        print(f" - Ingested batch {i // batch_size + 1}/{(len(events) - 1) // batch_size + 1}")

    print("Historical data ingestion completed successfully!")

if __name__ == '__main__':
    ingest_data()
