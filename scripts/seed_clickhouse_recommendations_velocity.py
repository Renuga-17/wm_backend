import os
import sys
import django
import random
import uuid
from datetime import datetime, date, timedelta

# Set up Django environment
sys.path.append("c:\\Users\\vidhyaadaran\\wm_backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from integrations.clickhouse_client import ClickHouseClient

def fetch_master_data():
    print("Fetching master data from PostgreSQL...")
    products = []
    product_categories = {}
    bins = []
    
    with connection.cursor() as cursor:
        # Fetch categories
        cursor.execute("SELECT id, name FROM product_categories;")
        cat_rows = cursor.fetchall()
        for cid, name in cat_rows:
            product_categories[cid] = name
            
        # Fetch products
        cursor.execute("SELECT id, sku, category_id FROM products;")
        prod_rows = cursor.fetchall()
        for pid, sku, cat_id in prod_rows:
            products.append({
                'id': str(pid),
                'sku': sku,
                'category_id': cat_id,
                'category_name': product_categories.get(cat_id, 'Unknown')
            })
            
        # Fetch bins
        cursor.execute("SELECT id FROM bins;")
        bin_rows = cursor.fetchall()
        for brow in bin_rows:
            bins.append(str(brow[0]))
            
    print(f"Retrieved {len(products)} products, {len(product_categories)} categories, and {len(bins)} bins from PostgreSQL.")
    return products, bins

def seed_recommendations(products, bins, client):
    print("Generating AI Recommendation Events...")
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=30)
    
    events = []
    
    models = ['xgb-slotting-v1.0', 'xgb-slotting-v1.1', 'dl-placement-v2.0']
    devices = ['cpu', 'gpu']
    reasonings = [
        "Optimal temperature alignment based on product requirements",
        "Minimize travel time to high velocity picking zones",
        "Heavy item placement recommended for lower tier shelf",
        "Lightweight item placement recommended for upper tier shelf",
        "High affinity co-location with related product category",
        "Safety isolation requirement for category items",
        "Fast-moving category assigned closer to loading dock"
    ]
    
    current_time = start_time
    total_inserted = 0
    
    # Generate random recommendation events across the 30-day timeline
    while current_time <= end_time:
        num_events_today = random.randint(80, 120)
        for _ in range(num_events_today):
            event_time = current_time + timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
                microseconds=random.randint(0, 999) * 1000
            )
            
            if event_time > end_time:
                continue
                
            prod = random.choice(products)
            rec_bin = random.choice(bins)
            
            is_accepted = 1 if random.random() < 0.82 else 0
            override_bin = None
            if is_accepted == 0:
                override_bin = random.choice(bins)
                while override_bin == rec_bin:
                    override_bin = random.choice(bins)
            
            metadata = {
                "inference_device": random.choice(devices),
                "is_hazardous": "true" if prod['category_name'].lower() == 'hazardous' else "false"
            }
            
            events.append([
                str(uuid.uuid4()),
                event_time,
                prod['id'],
                random.randint(1, 50),
                random.choice(models),
                rec_bin,
                round(random.uniform(0.40, 0.99), 4),
                random.choice(reasonings),
                is_accepted,
                override_bin,
                random.randint(15, 250),
                metadata
            ])
            
        current_time += timedelta(days=1)
        
    print(f"Generated {len(events)} recommendation events. Inserting into ClickHouse...")
    rec_cols = [
        'recommendation_id', 'timestamp', 'product_id', 'requested_quantity',
        'model_version', 'recommended_bin_id', 'confidence_score', 'reasoning',
        'is_accepted', 'override_bin_id', 'response_time_ms', 'metadata'
    ]
    
    batch_size = 2000
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        client.insert('ai_recommendation_events', batch, column_names=rec_cols)
        print(f" - Ingested recommendations batch {i // batch_size + 1}/{(len(events) - 1) // batch_size + 1}")
        total_inserted += len(batch)
        
    print(f"Successfully seeded {total_inserted} recommendations in ClickHouse.")

def seed_sku_velocity(products, client):
    print("Generating SKU Velocity Analytics...")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    records = []
    
    # Assign each product a random base velocity profile for consistency
    product_profiles = {}
    for prod in products:
        profile = random.choices(['FAST', 'MEDIUM', 'SLOW'], weights=[0.15, 0.35, 0.50])[0]
        product_profiles[prod['id']] = profile
        
    current_date = start_date
    total_inserted = 0
    
    while current_date <= end_date:
        for prod in products:
            profile = product_profiles[prod['id']]
            
            if profile == 'FAST':
                total_picks = random.randint(50, 150)
                total_putaways = random.randint(10, 30)
                turnover = round(random.uniform(4.0, 8.0), 2)
            elif profile == 'MEDIUM':
                total_picks = random.randint(10, 49)
                total_putaways = random.randint(2, 12)
                turnover = round(random.uniform(1.5, 3.9), 2)
            else:  # SLOW
                total_picks = random.randint(0, 9)
                total_putaways = random.randint(0, 3)
                turnover = round(random.uniform(0.0, 1.4), 2)
                
            total_picked_qty = total_picks * random.randint(2, 5)
            total_putaway_qty = total_putaways * random.randint(4, 10)
            
            records.append([
                current_date,
                prod['id'],
                prod['sku'],
                prod['category_name'],
                total_picks,
                total_picked_qty,
                total_putaways,
                total_putaway_qty,
                turnover,
                profile
            ])
            
        current_date += timedelta(days=1)
        
    print(f"Generated {len(records)} SKU velocity records. Inserting into ClickHouse...")
    velocity_cols = [
        'date', 'product_id', 'sku', 'category_name', 'total_picks',
        'total_picked_quantity', 'total_putaways', 'total_putaway_quantity',
        'inventory_turnover_rate', 'velocity_class'
    ]
    
    batch_size = 2000
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        client.insert('sku_velocity_analytics', batch, column_names=velocity_cols)
        print(f" - Ingested velocity batch {i // batch_size + 1}/{(len(records) - 1) // batch_size + 1}")
        total_inserted += len(batch)
        
    print(f"Successfully seeded {total_inserted} SKU velocity records in ClickHouse.")

def main():
    products, bins = fetch_master_data()
    if not products:
        print("Error: No products fetched from PostgreSQL. Aborting.")
        return
    if not bins:
        print("Error: No bins fetched from PostgreSQL. Aborting.")
        return
        
    ch_client = ClickHouseClient()
    client = ch_client.connect()
    
    seed_recommendations(products, bins, client)
    seed_sku_velocity(products, client)
    
    print("\nClickHouse tables successfully seeded!")

if __name__ == '__main__':
    main()
