import os
import sys
import django
from datetime import datetime, timedelta

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.warehouse.infrastructure.persistence.models import Warehouse
from apps.inventory.analytics_service import WarehouseAnalyticsService

def verify_analytics():
    print("======================================================================")
    print("           STARTING CLICKHOUSE ANALYTICS ENGINE VERIFICATION         ")
    print("======================================================================")

    # 1. Retrieve first warehouse
    warehouse = Warehouse.objects.first()
    if not warehouse:
        print("Error: No warehouse found in PostgreSQL. Please run PostgreSQL seeder first.")
        sys.exit(1)
    
    warehouse_id = str(warehouse.id)
    print(f"Testing analytics for Warehouse: {warehouse.name} ({warehouse_id})")

    # Time frame setup (last 30 days)
    end_str = datetime.utcnow().isoformat() + "Z"
    start_str = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"

    print("\n--- STEP 1: Verifying Spatial Heatmaps API Heuristic ---")
    heatmaps = WarehouseAnalyticsService.get_spatial_heatmap(warehouse_id, start_str, end_str)
    print(f"Retrieved {len(heatmaps)} heatmap segment records.")
    
    if heatmaps:
        first = heatmaps[0]
        print(f"Sample Heatmap: Zone: {first['zone_code']} | Aisle: {first['aisle_code']} | Total Activity: {first['total_activity']} | Avg Congestion: {first['avg_congestion']}")
        # Assert structure
        required_keys = {'zone_code', 'aisle_code', 'total_activity', 'avg_pick_time_sec', 'avg_congestion'}
        assert required_keys.issubset(first.keys()), f"Heatmap record missing keys. Got: {first.keys()}"
    else:
        print("Warning: Heatmap returned empty list.")

    print("\n--- STEP 2: Verifying Route Traversal & Efficiency Metrics ---")
    efficiency = WarehouseAnalyticsService.get_route_efficiency(warehouse_id, start_str, end_str)
    print(f"Total Routes Run: {efficiency.get('total_routes')}")
    print(f"Overall A* Route Optimization Rate: {efficiency.get('overall_optimization_rate')}%")
    print(f"Average Traversal Duration: {efficiency.get('avg_travel_time_seconds')} seconds")
    
    # Assert structure
    required_keys = {'total_routes', 'avg_distance_meters', 'avg_travel_time_seconds', 'overall_optimization_rate', 'vehicle_breakdown'}
    assert required_keys.issubset(efficiency.keys()), f"Efficiency dictionary missing keys. Got: {efficiency.keys()}"
    
    if efficiency.get('vehicle_breakdown'):
        v_break = efficiency['vehicle_breakdown']
        for vehicle, stats in list(v_break.items())[:2]:
            print(f"Vehicle: {vehicle} | Routes: {stats['route_count']} | Avg Travel Time: {stats['avg_travel_time_seconds']}s")

    print("\n--- STEP 3: Verifying Zone Environmental Telemetry Summary ---")
    telemetry = WarehouseAnalyticsService.get_sensor_telemetry_summary(warehouse_id, start_str, end_str)
    print(f"Retrieved telemetry aggregates for {len(telemetry)} zones.")
    
    if telemetry:
        sample = telemetry[0]
        print(f"Zone: {sample['zone_code']} | Avg Temp: {sample['avg_temperature']}C | Avg Humidity: {sample['avg_humidity']}% | Readings: {sample['reading_count']} | Warnings: {sample['warnings_count']}")
        # Assert structure
        required_keys = {'zone_code', 'avg_temperature', 'min_temperature', 'max_temperature', 'avg_humidity', 'avg_vibration', 'reading_count', 'warnings_count'}
        assert required_keys.issubset(sample.keys()), f"Telemetry record missing keys. Got: {sample.keys()}"

    print("\n--- STEP 4: Verifying Inventory Throughput & Transaction Volume ---")
    throughput = WarehouseAnalyticsService.get_inventory_throughput(warehouse_id, start_str, end_str)
    
    summary = throughput.get('summary', {})
    print(f"Total Picks Quantity: {summary.get('PICK', {}).get('total_quantity')}")
    print(f"Total Putaways Quantity: {summary.get('PUTAWAY', {}).get('total_quantity')}")
    
    timeline = throughput.get('timeline', [])
    print(f"Timeline Days Logged: {len(timeline)}")
    if timeline:
        t_first = timeline[0]
        print(f"Timeline First Day ({t_first['date']}) -> Picks: {t_first['picks_qty']} | Putaways: {t_first['putaways_qty']}")
        
    top_p = throughput.get('top_products', [])
    print(f"Top Moving SKUs count: {len(top_p)}")
    if top_p:
        print(f"Top SKU: {top_p[0]['sku']} | Vol: {top_p[0]['volume']}")

    # Assert structure
    required_keys = {'summary', 'top_products', 'timeline'}
    assert required_keys.issubset(throughput.keys()), f"Throughput dict missing keys. Got: {throughput.keys()}"

    print("\n======================================================================")
    print("      VERIFICATION COMPLETED SUCCESSFULLY - CLICKHOUSE ANALYTICS OK   ")
    print("======================================================================")

if __name__ == '__main__':
    verify_analytics()
