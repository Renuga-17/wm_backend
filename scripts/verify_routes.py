import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def create_table_if_not_exists():
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS navigation_graph (
                node_id UUID PRIMARY KEY,
                warehouse_id UUID REFERENCES warehouses(warehouse_id),
                node_name VARCHAR(100),
                node_type VARCHAR(50),
                x NUMERIC(10, 4),
                y NUMERIC(10, 4),
                z NUMERIC(10, 4),
                connections JSONB
            );
        """)

create_table_if_not_exists()

from apps.warehouse.infrastructure.persistence.models import Warehouse, NavigationNode
from apps.warehouse.application.services.pathfinding import PathfindingService

def test_routes():
    warehouse = Warehouse.objects.first()
    if not warehouse:
        warehouse = Warehouse.objects.create(name="Test Warehouse Route")
    
    # Create some NavigationNodes
    node_a = NavigationNode.objects.create(
        warehouse=warehouse, node_name="DOCK_A", node_type="DOCK", x=0, y=0, z=0
    )
    node_b = NavigationNode.objects.create(
        warehouse=warehouse, node_name="INTER_1", node_type="INTERSECTION", x=10, y=0, z=0
    )
    node_c = NavigationNode.objects.create(
        warehouse=warehouse, node_name="RACK_A1", node_type="RACK", x=10, y=10, z=0
    )
    
    # Set connections
    node_a.connections = [{"node_id": str(node_b.id), "weight": 10}]
    node_a.save()
    
    node_b.connections = [{"node_id": str(node_a.id), "weight": 10}, {"node_id": str(node_c.id), "weight": 10}]
    node_b.save()
    
    node_c.connections = [{"node_id": str(node_b.id), "weight": 10}]
    node_c.save()
    
    # Test pathfinding
    dist, path = PathfindingService.a_star_search(warehouse.id, node_a, node_c)
    print(f"Distance: {dist}")
    print(f"Path: {[p.node_name for p in path]}")
    
    # Cleanup
    node_a.delete()
    node_b.delete()
    node_c.delete()

if __name__ == "__main__":
    test_routes()
