import os
import sys
import django
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from apps.inventory.infrastructure.persistence.models import Product
from apps.warehouse.infrastructure.persistence.models import Warehouse
from apps.warehouse.infrastructure.persistence.models import Zone
from apps.warehouse.infrastructure.persistence.models import Bin
from integrations.clickhouse_client import ClickHouseClient

def seed_clickhouse():
    print("==========================================================")
    # 1. Initialize ClickHouse client
    ch_client = ClickHouseClient()
    client = ch_client.connect()
    if not client:
        print("Error: Could not connect to ClickHouse. Exiting.")
        sys.exit(1)

    print("Truncating existing ClickHouse tables...")
    tables_to_truncate = [
        'sensor_events',
        'warehouse_heatmaps',
        'route_analytics',
        'inventory_events',
        'scan_events',
        'ai_predictions',
        'demand_forecasts'
    ]
    for table in tables_to_truncate:
        try:
            client.query(f"TRUNCATE TABLE {table}")
            print(f" - Truncated table: {table}")
        except Exception as e:
            print(f" - Warning: Failed to truncate {table}: {e}")

    # 2. Fetch PostgreSQL master data
    print("\nFetching master data from PostgreSQL...")
    products = list(Product.objects.all())
    zones = list(Zone.objects.select_related('warehouse'))
    bins = list(Bin.objects.select_related('shelf', 'shelf__rack', 'shelf__rack__zone'))
    
    if not products or not zones or not bins:
        print("Error: PostgreSQL database is missing products, zones, or bins. Run migrations and seed PostgreSQL first.")
        sys.exit(1)

    print(f"Loaded: {len(products)} products, {len(zones)} zones, {len(bins)} bins.")

    warehouse = zones[0].warehouse
    warehouse_id = str(warehouse.id)
    print(f"Targeting Warehouse: {warehouse.name} ({warehouse_id})")

    # Time frame setup (30 days of data, 1 hour interval for telemetry)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=30)
    current_time = start_time

    # Pre-aggregate data for generation speed
    zone_codes = [z.zone_name for z in zones]
    product_data = [{'id': str(p.id), 'sku': p.sku, 'name': p.product_name} for p in products]
    bin_data = [{'id': str(b.id), 'code': b.bin_code, 'zone': b.shelf.rack.zone.zone_name, 'rack': b.shelf.rack.rack_code, 'shelf': str(b.shelf.shelf_number)} for b in bins]

    # Containers for batch insertion
    sensor_events = []
    warehouse_heatmaps = []
    route_analytics = []
    inventory_events = []
    scan_events = []
    ai_predictions = []
    demand_forecasts = []

    print("\nGenerating simulated analytics data...")

    # For SKU-specific velocity calculations
    product_profiles = {}
    for p in product_data:
        # Assign products dynamic velocity profiles
        product_profiles[p['id']] = random.choices(['FAST', 'MEDIUM', 'SLOW'], weights=[0.15, 0.35, 0.50])[0]

    # Iterate day-by-day or hour-by-hour to simulate realistic logs
    while current_time <= end_time:
        day_date = current_time.date()
        hour = current_time.hour
        is_peak = 8 <= hour <= 18
        
        # Determine scale of events based on time (more during business hours)
        activity_multiplier = 4 if is_peak else 1
        
        # --- 1. Hourly Sensor Events (IoT telemetry) ---
        for zone in zones:
            zname = zone.zone_name
            ztype = zone.zone_type
            
            # Simulated sensor readings
            if ztype == 'COLD':
                temp = float(round(random.uniform(1.0, 5.0), 2))
                humidity = float(round(random.uniform(75.0, 85.0), 2))
            elif ztype == 'HAZARDOUS':
                temp = float(round(random.uniform(15.0, 18.0), 2))
                humidity = float(round(random.uniform(30.0, 45.0), 2))
            else: # DRY / PICKING / STORAGE
                temp = float(round(random.uniform(19.0, 24.0), 2))
                humidity = float(round(random.uniform(45.0, 55.0), 2))
                
            vibration = float(round(random.uniform(0.01, 0.25), 3))
            status = 'OK'
            if temp > 25.0 or (ztype == 'COLD' and temp > 6.0):
                status = 'WARNING'
                
            sensor_events.append([
                f"temp-{zname}",
                current_time,
                "TEMPERATURE",
                zname,
                temp,
                humidity,
                vibration,
                status
            ])
            sensor_events.append([
                f"humid-{zname}",
                current_time,
                "HUMIDITY",
                zname,
                temp,
                humidity,
                vibration,
                status
            ])

        # --- 2. Hourly Warehouse Heatmap Snapshots ---
        for zone in zones:
            zname = zone.zone_name
            # Generate metrics for a few aisles in this zone
            for aisle in ['Aisle-01', 'Aisle-02']:
                activity_count = random.randint(5, 30) * activity_multiplier
                avg_pick_time = float(round(random.uniform(15.0, 45.0), 2))
                congestion_score = float(round(min(activity_count / 100.0 + random.uniform(0.0, 0.2), 1.0), 2))
                
                warehouse_heatmaps.append([
                    current_time,
                    zname,
                    aisle,
                    activity_count,
                    avg_pick_time,
                    congestion_score
                ])

        # --- 3. Inventory movements & scan events (simulated picking and putaway) ---
        movements_count = random.randint(3, 10) * activity_multiplier
        for _ in range(movements_count):
            prod = random.choice(product_data)
            v_profile = product_profiles[prod['id']]
            
            # Skip slow products occasionally to simulate velocity differences
            if v_profile == 'SLOW' and random.random() > 0.1:
                continue
                
            qty = random.randint(1, 10) if v_profile != 'FAST' else random.randint(5, 50)
            m_type = random.choice(['PICK', 'PUTAWAY'])
            
            # Select random bin
            b = random.choice(bin_data)
            
            event_id = uuid.uuid4()
            confidence = float(round(random.uniform(0.85, 0.99), 2))
            
            # 1. Inventory Event
            inventory_events.append([
                event_id,
                current_time,
                "STOCK_CHANGE",
                prod['id'],
                prod['sku'],
                prod['name'],
                qty,
                warehouse_id,
                b['zone'],
                b['rack'],
                b['shelf'],
                b['code'],
                "RECEIVING" if m_type == 'PUTAWAY' else b['code'],
                b['code'] if m_type == 'PUTAWAY' else "SHIPPING",
                m_type,
                "worker-robot-01",
                1 if random.random() > 0.2 else 0, # AI-generated decision
                confidence
            ])
            
            # 2. Match Scan Events
            scan_events.append([
                uuid.uuid4(),
                current_time - timedelta(seconds=random.randint(1, 10)),
                "BARCODE",
                prod['id'],
                prod['sku'],
                b['zone'],
                b['rack'],
                b['shelf'],
                b['code'],
                "handheld-scanner-04",
                "user-worker-12",
                "SUCCESS"
            ])

        # --- 4. Route Analytics (Forklift/AGV traversals) ---
        routes_in_hour = random.randint(1, 4) * activity_multiplier
        for _ in range(routes_in_hour):
            dist = float(round(random.uniform(10.0, 150.0), 1))
            congestion = float(round(random.uniform(0.0, 0.6), 2))
            
            # Travel time proportional to distance + congestion delay
            travel_time = (dist / 1.5) * (1.0 + congestion)
            
            route_analytics.append([
                uuid.uuid4(),
                current_time,
                random.choice(["AGV", "FORKLIFT", "MANUAL_JACK"]),
                random.choice(zone_codes),
                random.choice(zone_codes),
                dist,
                float(round(travel_time, 1)),
                congestion,
                1 if random.random() > 0.3 else 0 # Optimized by A* router
            ])

        # Increment hour
        current_time += timedelta(hours=1)

    # --- 5. Generate daily/one-off events (AI Predictions & Demand Forecasts) ---
    print("Generating AI Predictions & Demand Forecast aggregates...")
    for prod in product_data:
        v_profile = product_profiles[prod['id']]
        pred_demand = 0
        if v_profile == 'FAST':
            pred_demand = random.randint(500, 1500)
            conf = float(round(random.uniform(0.85, 0.95), 2))
        elif v_profile == 'MEDIUM':
            pred_demand = random.randint(100, 499)
            conf = float(round(random.uniform(0.80, 0.90), 2))
        else:
            pred_demand = random.randint(5, 99)
            conf = float(round(random.uniform(0.70, 0.85), 2))

        # Demand Forecast entry
        demand_forecasts.append([
            end_time,
            prod['id'],
            pred_demand,
            30, # forecast window
            conf
        ])

        # AI Recommendations predictions (up to 3 per product)
        for i in range(random.randint(1, 3)):
            rand_bin = random.choice(bin_data)
            ai_predictions.append([
                uuid.uuid4(),
                end_time - timedelta(days=random.randint(0, 20)),
                "xgb-slotting-v2.0",
                "PLACEMENT",
                prod['id'],
                rand_bin['zone'],
                rand_bin['code'],
                float(round(random.uniform(0.50, 0.95), 2)), # utilization score
                float(round(random.uniform(10.0, 120.0), 2)), # travel distance
                float(round(random.uniform(0.75, 0.99), 2)), # confidence score
                '{"reasoning": "High demand items near docking zone", "congestion_avoided": true}'
            ])

    # 3. Batch Inserts to ClickHouse
    print(f"\nSeeding database with generated rows:")
    
    # 1. sensor_events
    print(f" - Inserting {len(sensor_events)} sensor_events records...")
    client.insert('sensor_events', sensor_events, column_names=[
        'sensor_id', 'event_time', 'sensor_type', 'zone_code', 
        'temperature', 'humidity', 'vibration', 'status'
    ])

    # 2. warehouse_heatmaps
    print(f" - Inserting {len(warehouse_heatmaps)} warehouse_heatmaps records...")
    client.insert('warehouse_heatmaps', warehouse_heatmaps, column_names=[
        'heatmap_time', 'zone_code', 'aisle_code', 'activity_count', 
        'avg_pick_time', 'congestion_score'
    ])

    # 3. route_analytics
    print(f" - Inserting {len(route_analytics)} route_analytics records...")
    client.insert('route_analytics', route_analytics, column_names=[
        'route_id', 'route_time', 'vehicle_type', 'source_zone', 
        'destination_zone', 'distance_meters', 'travel_time_seconds', 
        'congestion_level', 'optimized'
    ])

    # 4. inventory_events
    print(f" - Inserting {len(inventory_events)} inventory_events records...")
    client.insert('inventory_events', inventory_events, column_names=[
        'event_id', 'event_time', 'event_type', 'product_id', 'sku', 'product_name',
        'quantity', 'warehouse_id', 'zone_code', 'rack_code', 'shelf_code', 'bin_code',
        'source_location', 'destination_location', 'movement_type', 'user_id', 
        'ai_generated', 'confidence_score'
    ])

    # 5. scan_events
    print(f" - Inserting {len(scan_events)} scan_events records...")
    client.insert('scan_events', scan_events, column_names=[
        'scan_id', 'scan_time', 'scan_type', 'product_id', 'sku', 'zone_code',
        'rack_code', 'shelf_code', 'bin_code', 'device_id', 'worker_id', 'scan_status'
    ])

    # 6. ai_predictions
    print(f" - Inserting {len(ai_predictions)} ai_predictions records...")
    client.insert('ai_predictions', ai_predictions, column_names=[
        'prediction_id', 'prediction_time', 'model_name', 'prediction_type', 'product_id',
        'recommended_zone', 'recommended_bin', 'utilization_score', 'travel_distance',
        'confidence_score', 'prediction_data'
    ])

    # 7. demand_forecasts
    print(f" - Inserting {len(demand_forecasts)} demand_forecasts records...")
    client.insert('demand_forecasts', demand_forecasts, column_names=[
        'forecast_time', 'product_id', 'predicted_demand', 'forecast_window_days', 'confidence_score'
    ])

    print("\n==========================================================")
    print("      CLICKHOUSE ANALYTICS DATA SEEDING COMPLETE!        ")
    print("==========================================================")

if __name__ == '__main__':
    seed_clickhouse()
