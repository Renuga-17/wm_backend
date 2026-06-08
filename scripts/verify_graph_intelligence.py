import os
import django
import sys
import math

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.warehouse.infrastructure.persistence.models import Warehouse, NavigationNode, NavigationEdge
from apps.warehouse.infrastructure.persistence.models import OptimizedRoute, RouteSegment
from apps.warehouse.services.pathfinding import PathfindingService

def run_verification():
    print("======================================================================")
    print("     STARTING ADVANCED WAREHOUSE GRAPH INTELLIGENCE VERIFICATION      ")
    print("======================================================================")

    # 1. Fetch or create a warehouse
    warehouse = Warehouse.objects.first()
    if not warehouse:
        warehouse = Warehouse.objects.create(name="Graph Intelligence Test Warehouse")
    print(f"Using Warehouse: {warehouse.name} ({warehouse.id})")

    # Clean up any residual nodes from previous failed tests
    NavigationNode.objects.filter(node_name__in=["DOCK_A", "INTER_1", "INTER_ALT", "RACK_A1"]).delete()

    print("\n--- STEP 1: Creating Navigation Nodes & Graph Topology ---")
    # Short Route: DOCK_A <-> INTER_1 <-> RACK_A1 (total distance = 20)
    node_a = NavigationNode.objects.create(
        warehouse=warehouse, node_name="DOCK_A", node_type="DOCK", x=0, y=0, z=0
    )
    node_b = NavigationNode.objects.create(
        warehouse=warehouse, node_name="INTER_1", node_type="INTERSECTION", x=10, y=0, z=0
    )
    node_c = NavigationNode.objects.create(
        warehouse=warehouse, node_name="RACK_A1", node_type="RACK", x=10, y=10, z=0
    )

    # Alternate (Longer) Route: DOCK_A <-> INTER_ALT <-> RACK_A1 (total distance = 30)
    node_alt = NavigationNode.objects.create(
        warehouse=warehouse, node_name="INTER_ALT", node_type="INTERSECTION", x=0, y=15, z=0
    )

    # Define connections in JSON (for self-healing bootstrapping)
    node_a.connections = [
        {"node_id": str(node_b.id), "weight": 10.0},
        {"node_id": str(node_alt.id), "weight": 15.0}
    ]
    node_a.save()

    node_b.connections = [
        {"node_id": str(node_a.id), "weight": 10.0},
        {"node_id": str(node_c.id), "weight": 10.0}
    ]
    node_b.save()

    node_alt.connections = [
        {"node_id": str(node_a.id), "weight": 15.0},
        {"node_id": str(node_c.id), "weight": 15.0}
    ]
    node_alt.save()

    node_c.connections = [
        {"node_id": str(node_b.id), "weight": 10.0},
        {"node_id": str(node_alt.id), "weight": 15.0}
    ]
    node_c.save()

    print("Nodes and JSON connections created successfully!")

    print("\n--- STEP 2: Verifying Self-Healing Adjacency Bootstrapping ---")
    # Trigger graph construction which bootstraps NavigationEdge entries
    nodes_map, graph = PathfindingService.get_graph(warehouse.id)
    
    # Assert NavigationEdge rows exist
    edges = NavigationEdge.objects.filter(warehouse_id=warehouse.id)
    print(f"Successfully bootstrapped {edges.count()} NavigationEdge records in the database.")
    assert edges.count() > 0, "Self-healing bootstrapper failed to create edges!"

    print("\n--- STEP 3: Finding Shortest Path (Base Case) ---")
    dist, path = PathfindingService.a_star_search(warehouse.id, node_a, node_c)
    path_names = [p.node_name for p in path]
    print(f"Base Shortest Distance: {dist}")
    print(f"Base Path: {path_names}")
    assert path_names == ["DOCK_A", "INTER_1", "RACK_A1"], "Pathfinding should have picked the shorter INTER_1 route!"

    print("\n--- STEP 4: Simulating Dynamic Block & Congestion Cost ---")
    # Block the edge from INTER_1 to RACK_A1
    edge_to_block = NavigationEdge.objects.filter(
        warehouse_id=warehouse.id, from_node=node_b, to_node=node_c
    ).first()
    assert edge_to_block is not None, "Edge from INTER_1 to RACK_A1 not found!"
    
    edge_to_block.is_blocked = True
    edge_to_block.save()
    print(f"Blocked edge: {edge_to_block.from_node.node_name} -> {edge_to_block.to_node.node_name}")

    # Mirror blocking for bidirectional realism
    reciprocal_edge = NavigationEdge.objects.filter(
        warehouse_id=warehouse.id, from_node=node_c, to_node=node_b
    ).first()
    if reciprocal_edge:
        reciprocal_edge.is_blocked = True
        reciprocal_edge.save()

    print("\n--- STEP 5: Verifying Dynamic Traffic-Aware Path Recalculation ---")
    new_dist, new_path = PathfindingService.a_star_search(warehouse.id, node_a, node_c)
    new_path_names = [p.node_name for p in new_path]
    print(f"New Dynamic Distance: {new_dist}")
    print(f"New Dynamic Path: {new_path_names}")
    assert new_path_names == ["DOCK_A", "INTER_ALT", "RACK_A1"], "A* failed to reroute around blocked corridor!"
    print("SUCCESS: A* dynamically recalculated route to bypass the blocked corridor!")

    print("\n--- STEP 6: Testing ORM Recalculation Service integration ---")
    # Let's create a route record in the DB and verify it gets recalculated programmatically
    route = OptimizedRoute.objects.create(
        warehouse=warehouse,
        start_location="DOCK_A",
        distance=20.0,
        estimated_time=13
    )
    # Populate original segment order
    RouteSegment.objects.create(route=route, segment_order=0, x=node_a.x, y=node_a.y)
    RouteSegment.objects.create(route=route, segment_order=1, x=node_b.x, y=node_b.y)
    RouteSegment.objects.create(route=route, segment_order=2, x=node_c.x, y=node_c.y)

    print(f"Created route {route.id} with original physical distance {route.distance}")

    # Now let's trigger recalculation programmatically (simulating POST /api/routes/recalculate)
    # Using PathfindingService directly or testing A* updates
    recalc_dist, recalc_path = PathfindingService.a_star_search(warehouse.id, node_a, node_c)
    route.distance = recalc_dist
    route.estimated_time = int(recalc_dist / 1.5)
    route.save()
    route.segments.all().delete()
    for idx, nd in enumerate(recalc_path):
        RouteSegment.objects.create(route=route, segment_order=idx, x=nd.x, y=nd.y)

    print(f"Recalculated route distance is now: {route.distance}")
    segments = list(route.segments.all().order_by('segment_order'))
    print(f"Recalculated Route Segments count: {len(segments)}")
    assert len(segments) == 3, "New recalculated path should have 3 nodes."
    assert float(route.distance) == 30.0, "New route distance must match the alternate path distance (30.0)"

    print("\n--- STEP 7: Cleaning Up Verification Resources ---")
    node_a.delete()
    node_b.delete()
    node_c.delete()
    node_alt.delete()
    route.delete()
    print("Cleanup completed successfully.")

    print("\n======================================================================")
    print("      VERIFICATION COMPLETED SUCCESSFULY - GRAPH INTELLIGENCE OK       ")
    print("======================================================================")

if __name__ == "__main__":
    run_verification()
