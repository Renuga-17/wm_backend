import os
import django
import sys
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.warehouse.infrastructure.persistence.models import Warehouse, NavigationNode, Rack
from apps.warehouse.infrastructure.persistence.models import Zone
from apps.warehouse.infrastructure.persistence.models import Shelf, Bin
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory
from apps.inventory.infrastructure.persistence.models import StockMovement
from apps.inventory.ai_engine.ml_slotting import AISlottingEngine
from apps.inventory.infrastructure.persistence.models import DemandForecast, CongestionPrediction, SlottingScore, AllocationRecommendation

def run_verification():
    print("======================================================================")
    print("           STARTING AI SLOTTING ENGINE V2 VERIFICATION               ")
    print("======================================================================")

    # 1. Fetch/Create Warehouse
    warehouse = Warehouse.objects.first()
    if not warehouse:
        warehouse = Warehouse.objects.create(name="AI Slotting Test Warehouse")
    print(f"Warehouse: {warehouse.name} ({warehouse.id})")

    # Clean up leftovers
    Product.objects.filter(sku__in=["SKU_HOT_ITEM", "SKU_COLD_ITEM", "SKU_HEAVY_ITEM"]).delete()
    Zone.objects.filter(zone_name__in=["ZONE_PICKING_A", "ZONE_PICKING_B"]).delete()

    print("\n--- STEP 1: Creating Zone & Shelf Grid ---")
    zone_a = Zone.objects.create(
        warehouse=warehouse, zone_name="ZONE_PICKING_A", zone_type="PICKING",
        x=0, y=0, z=0, width=10, height=10, depth=10
    )
    zone_b = Zone.objects.create(
        warehouse=warehouse, zone_name="ZONE_PICKING_B", zone_type="PICKING",
        x=20, y=20, z=0, width=10, height=10, depth=10
    )

    rack_a = Rack.objects.create(
        zone=zone_a, rack_code="RACK_SLOT_A", max_weight=500.0,
        x=2, y=2, z=0, width=5, height=5, depth=5, rotation_angle=0
    )
    rack_b = Rack.objects.create(
        zone=zone_b, rack_code="RACK_SLOT_B", max_weight=500.0,
        x=22, y=22, z=0, width=5, height=5, depth=5, rotation_angle=0
    )

    shelf_a = Shelf.objects.create(rack=rack_a, shelf_number=1, max_weight=200.0, height_from_ground=1.0)
    shelf_b = Shelf.objects.create(rack=rack_b, shelf_number=1, max_weight=50.0, height_from_ground=1.0) # Lower weight limit shelf

    bin_a = Bin.objects.create(shelf=shelf_a, bin_code="BIN_A_OPTIMAL", max_capacity=100.0, current_capacity=0, is_occupied=False)
    bin_b = Bin.objects.create(shelf=shelf_b, bin_code="BIN_B_LIGHTWEIGHT", max_capacity=100.0, current_capacity=0, is_occupied=False)

    print(f"Created bins: {bin_a.bin_code} (max shelf weight: 200) & {bin_b.bin_code} (max shelf weight: 50)")

    # Create Navigation Nodes to benchmark travel costs
    node_dock = NavigationNode.objects.create(
        warehouse=warehouse, node_name="DOCK_PICK", node_type="DOCK", x=0, y=0, z=0
    )
    node_bin_a = NavigationNode.objects.create(
        warehouse=warehouse, node_name="BIN_A_OPTIMAL", node_type="PICK_POINT", x=2, y=2, z=0
    )
    node_bin_b = NavigationNode.objects.create(
        warehouse=warehouse, node_name="BIN_B_LIGHTWEIGHT", node_type="PICK_POINT", x=22, y=22, z=0
    )

    print("\n--- STEP 2: Creating Products and Simulating Order Activity ---")
    category = ProductCategory.objects.first()
    if not category:
        category = ProductCategory.objects.create(category_name="Electronics")

    # SKU_HOT_ITEM: Fast Mover
    product_hot = Product.objects.create(
        category=category, sku="SKU_HOT_ITEM", product_name="Fast Moving Item", weight=10.0
    )
    # SKU_COLD_ITEM: Slow Mover
    product_cold = Product.objects.create(
        category=category, sku="SKU_COLD_ITEM", product_name="Slow Moving Item", weight=5.0
    )
    # SKU_HEAVY_ITEM: Exceeds shelf B limits
    product_heavy = Product.objects.create(
        category=category, sku="SKU_HEAVY_ITEM", product_name="Extremely Heavy Item", weight=150.0
    )

    # Simulate recent picks for hot SKU to train demand forecaster
    for i in range(10):
        StockMovement.objects.create(
            product=product_hot, quantity=5, movement_type='PICK'
        )

    print("Products created. Orders simulated for SKU_HOT_ITEM.")

    print("\n--- STEP 3: Executing Demand Forecasting ---")
    forecast_hot = AISlottingEngine.forecast_demand(product_hot.sku)
    forecast_cold = AISlottingEngine.forecast_demand(product_cold.sku)

    print(f"Hot SKU Forecast Demand Score: {forecast_hot.predicted_demand_score}")
    print(f"Cold SKU Forecast Demand Score: {forecast_cold.predicted_demand_score}")
    
    assert forecast_hot.predicted_demand_score > forecast_cold.predicted_demand_score, "Hot SKU demand forecast should be higher!"

    print("\n--- STEP 4: Executing Congestion Prediction ---")
    congestion_predictions = AISlottingEngine.predict_congestion_risk(warehouse.id)
    for risk in congestion_predictions:
        print(f"Zone: {risk.zone.zone_name} | Congestion Risk Probability: {risk.congestion_risk} | Recent Volume: {risk.predicted_traffic_volume}")

    print("\n--- STEP 5: Executing Multi-Factor AI Slotting Optimization ---")
    # Verify heavy item gets slotted onto shelf that can support its weight (> 150)
    rec_heavy = AISlottingEngine.optimize_slotting(product_heavy.sku, warehouse.id)
    print(f"Heavy Item Recommended Bin: {rec_heavy.recommended_bin.bin_code} (max shelf weight: {rec_heavy.recommended_bin.shelf.max_weight})")
    assert float(rec_heavy.recommended_bin.shelf.max_weight) >= float(product_heavy.weight), "Heavy item placed on shelf that cannot support its weight!"

    # Verify hot item gets successfully slotted
    rec_hot = AISlottingEngine.optimize_slotting(product_hot.sku, warehouse.id)
    print(f"Hot Item Recommended Bin: {rec_hot.recommended_bin.bin_code}")
    assert rec_hot.recommended_bin is not None, "Failed to recommend bin for hot SKU!"


    print("\n--- STEP 6: Cleaning Up Resources ---")
    product_hot.delete()
    product_cold.delete()
    product_heavy.delete()
    node_dock.delete()
    node_bin_a.delete()
    node_bin_b.delete()
    zone_a.delete()
    zone_b.delete()
    print("Cleanup completed.")

    print("\n======================================================================")
    print("        VERIFICATION COMPLETED SUCCESSFULLY - AI SLOTTING ENGINE OK   ")
    print("======================================================================")

if __name__ == "__main__":
    run_verification()
