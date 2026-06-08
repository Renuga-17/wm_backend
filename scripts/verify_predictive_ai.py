import os
import sys
import django
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.warehouse.infrastructure.persistence.models import Warehouse, NavigationNode, Rack
from apps.warehouse.infrastructure.persistence.models import Zone
from apps.warehouse.infrastructure.persistence.models import Shelf, Bin
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory
from apps.inventory.infrastructure.persistence.models import DemandForecast, CongestionPrediction, SlottingScore, SystemAlert
from apps.inventory.ai_engine.ml_slotting import AISlottingEngine
from apps.inventory.ai_engine.hotspot_prevention import HotspotPreventionEngine
from apps.inventory.ai_engine.operational_scoring import OperationalScoringEngine
from apps.inventory.ai_engine.feedback_loop import AIFeedbackLoop

from rest_framework.test import APIRequestFactory, force_authenticate
from apps.inventory.presentation.api.views import AIRecommendationViewSet
from apps.identity.infrastructure.persistence.models import User

def run_verification():
    print("======================================================================")
    print("      STARTING PHASE 10 PREDICTIVE AI SLOTTING VERIFICATION          ")
    print("======================================================================")

    # 1. Fetch/Create Warehouse
    warehouse = Warehouse.objects.first()
    if not warehouse:
        warehouse = Warehouse.objects.create(name="Predictive AI Test Warehouse")
    print(f"Warehouse: {warehouse.name} ({warehouse.id})")

    # Clean up leftovers
    Product.objects.filter(sku__in=["SKU_PRED_HOT", "SKU_PRED_COLD"]).delete()
    Zone.objects.filter(zone_name__in=["ZONE_PRED_A", "ZONE_PRED_B"]).delete()
    SystemAlert.objects.filter(zone_code__in=["ZONE_PRED_A", "ZONE_PRED_B"]).delete()

    print("\n--- STEP 1: Creating Layout Grid & Master Data ---")
    zone_a = Zone.objects.create(
        warehouse=warehouse, zone_name="ZONE_PRED_A", zone_type="PICKING",
        x=0, y=0, z=0, width=10, height=10, depth=10
    )
    zone_b = Zone.objects.create(
        warehouse=warehouse, zone_name="ZONE_PRED_B", zone_type="PICKING",
        x=20, y=20, z=0, width=10, height=10, depth=10
    )

    rack_a = Rack.objects.create(
        zone=zone_a, rack_code="RACK_PRED_A", max_weight=500.0,
        x=2, y=2, z=0, width=5, height=5, depth=5, rotation_angle=0
    )
    rack_b = Rack.objects.create(
        zone=zone_b, rack_code="RACK_PRED_B", max_weight=500.0,
        x=22, y=22, z=0, width=5, height=5, depth=5, rotation_angle=0
    )

    shelf_a = Shelf.objects.create(rack=rack_a, shelf_number=1, max_weight=200.0, height_from_ground=1.0)
    shelf_b = Shelf.objects.create(rack=rack_b, shelf_number=1, max_weight=200.0, height_from_ground=1.0)

    bin_a = Bin.objects.create(shelf=shelf_a, bin_code="BIN_PRED_A", max_capacity=100.0, current_capacity=0, is_occupied=False)
    bin_b = Bin.objects.create(shelf=shelf_b, bin_code="BIN_PRED_B", max_capacity=100.0, current_capacity=0, is_occupied=False)

    category = ProductCategory.objects.first()
    if not category:
        category = ProductCategory.objects.create(category_name="Electronics")

    product = Product.objects.create(
        category=category, sku="SKU_PRED_HOT", product_name="Predictive Hot Product", weight=10.0
    )

    print("Master records initialized successfully.")

    print("\n--- STEP 2: Verifying Placement Scoring API ---")
    scores = AISlottingEngine.calculate_all_slotting_scores(product.sku, warehouse.id)
    print(f"Computed scores for {len(scores)} candidate bins.")
    assert len(scores) >= 2, "Failed to score candidate bins!"
    for sc in scores[:2]:
        print(f" - Bin: {sc['bin_code']} | Score: {sc['score']} (Proximity: {sc['proximity_reward']}, Congestion: {sc['congestion_penalty']})")

    print("\n--- STEP 3: Verifying Hotspot Prevention Engine ---")
    # Simulate high occupancy to trigger a hotspot
    bin_a.is_occupied = True
    bin_a.save()

    # Seed a warning status sensor event in ClickHouse for ZONE_PRED_A to raise the risk score to >= 0.50
    try:
        from integrations.clickhouse_client import ClickHouseClient
        from django.utils import timezone
        ch_client = ClickHouseClient()
        client = ch_client.connect()
        if client:
            client.insert('sensor_events', [
                ["temp-ZONE_PRED_A", timezone.now(), "TEMPERATURE", "ZONE_PRED_A", 28.5, 55.0, 0.12, "WARNING"]
            ], column_names=['sensor_id', 'event_time', 'sensor_type', 'zone_code', 'temperature', 'humidity', 'vibration', 'status'])
            print("Successfully inserted temp WARNING event in ClickHouse for ZONE_PRED_A.")
    except Exception as e:
        print(f"ClickHouse direct seed failed: {e}")

    hotspots = HotspotPreventionEngine.analyze_hotspots(warehouse.id)
    print(f"Generated hotspot prevention analysis:")
    for h in hotspots:
        print(f" - Zone: {h['zone']} | Risk Score: {h['risk_score']} | Severity: {h['severity']} | Rec: {h['recommendation']}")
    
    # Assert alert was recorded
    alerts = SystemAlert.objects.filter(zone_code="ZONE_PRED_A")
    print(f"Database alerts created for Zone A: {alerts.count()}")
    assert alerts.count() > 0, "No alerts created in PostgreSQL!"

    print("\n--- STEP 4: Verifying Operational Scoring Engine ---")
    scores_kpis = OperationalScoringEngine.calculate_operational_scores(warehouse.id)
    print("Warehouse KPIs:")
    print(f" - Congestion score: {scores_kpis['congestion_score']}")
    print(f" - Efficiency score: {scores_kpis['efficiency_score']}")
    print(f" - Utilization score: {scores_kpis['utilization_score']}")
    print(f" - Accessibility score: {scores_kpis['accessibility_score']}")
    
    assert scores_kpis['utilization_score'] > 0.0, "Utilization score calculation should be positive!"

    print("\n--- STEP 5: Verifying AI Feedback Learning Loop ---")
    initial_weights = AIFeedbackLoop.get_current_weights()
    print(f"Initial travel cost weight: {initial_weights['travel_cost_factor']}")

    # Simulate feedback indicating slow picks
    res_feedback = AIFeedbackLoop.process_feedback_signal('PICK_DURATION', {
        'duration': 75.0,
        'benchmark': 40.0
    })
    new_weights = res_feedback['current_weights']
    print(f"Feedback result message: {res_feedback['message']}")
    print(f"Updated travel cost weight: {new_weights['travel_cost_factor']}")
    assert new_weights['travel_cost_factor'] > initial_weights['travel_cost_factor'], "Travel cost weight did not increase!"

    print("\n--- STEP 6: Verifying ViewSet Action Endpoints via APIRequestFactory ---")
    factory = APIRequestFactory()
    view = AIRecommendationViewSet.as_view({
        'get': 'slotting_score',
        'post': 'feedback'
    })
    
    # Setup test user for auth if needed
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(username="test_ai_user", email="ai@test.com", password="pwd")

    # 1. Test slotting-score endpoint
    request_score = factory.get(f'/api/ai/slotting-score/?product_id={product.sku}&warehouse_id={warehouse.id}')
    force_authenticate(request_score, user=user)
    response_score = view(request_score)
    print(f"GET /api/ai/slotting-score/ Status: {response_score.status_code}")
    assert response_score.status_code == 200, f"Expected 200, got {response_score.status_code}"
    print(f"Sample response: {response_score.data[0]}")

    # 2. Test feedback ingestion endpoint
    request_feed = factory.post('/api/ai/feedback/', {
        "signal_type": "RE_SLOT_FREQUENCY",
        "payload": {"re_slots_count": 8}
    }, format='json')
    force_authenticate(request_feed, user=user)
    response_feed = view(request_feed)
    print(f"POST /api/ai/feedback/ Status: {response_feed.status_code}")
    assert response_feed.status_code == 200, f"Expected 200, got {response_feed.status_code}"

    # 3. Test alerts resolution endpoint
    alert_to_resolve = SystemAlert.objects.filter(is_resolved=False).first()
    if alert_to_resolve:
        view_alerts = AIRecommendationViewSet.as_view({'post': 'alerts'})
        request_resolve = factory.post('/api/ai/alerts/', {"alert_id": str(alert_to_resolve.id)}, format='json')
        force_authenticate(request_resolve, user=user)
        response_resolve = view_alerts(request_resolve)
        print(f"POST /api/ai/alerts/ (resolve) Status: {response_resolve.status_code}")
        assert response_resolve.status_code == 200, f"Expected 200, got {response_resolve.status_code}"
        
        # Verify state in DB
        alert_to_resolve.refresh_from_db()
        assert alert_to_resolve.is_resolved == True, "Alert state was not updated to resolved!"

    print("\n--- STEP 7: Cleaning Up Verification Resources ---")
    product.delete()
    zone_a.delete()
    zone_b.delete()
    print("Cleanup completed.")

    print("\n======================================================================")
    print("      VERIFICATION COMPLETED SUCCESSFULLY - PREDICTIVE AI ENGINE OK   ")
    print("======================================================================")

if __name__ == '__main__':
    run_verification()
