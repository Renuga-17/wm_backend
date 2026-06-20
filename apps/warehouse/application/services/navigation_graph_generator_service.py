import math
from decimal import Decimal
from apps.warehouse.models import Warehouse, Bin, Rack, NavigationNode, NavigationEdge, StorageLocationNodeMap

class NavigationGraphGeneratorService:
    @staticmethod
    def generate_navigation_graph(warehouse: Warehouse, path_entities=None):
        """
        Parses path lines, creates NavigationNodes & NavigationEdges, 
        and links Bins to the nearest NavigationNode.
        """
        if path_entities is None:
            path_entities = []

        # Find or create start gate (Dock)
        dock_node, _ = NavigationNode.objects.get_or_create(
            warehouse=warehouse,
            node_name='DOCK_MAIN',
            defaults={
                'node_type': 'DOCK',
                'x': Decimal('0.00'),
                'y': Decimal('0.00'),
                'z': Decimal('0.00')
            }
        )

        created_nodes = [dock_node]

        # 1. Generate nodes from CAD path polylines/lines
        for idx, ent in enumerate(path_entities):
            points = ent.get('points', [])
            seg_nodes = []
            for p_idx, pt in enumerate(points):
                node_name = f"PATH-NODE-{idx}-{p_idx}"
                # Delete existing if names clash
                NavigationNode.objects.filter(warehouse=warehouse, node_name=node_name).delete()
                
                node = NavigationNode.objects.create(
                    warehouse=warehouse,
                    node_name=node_name,
                    node_type='PATH_POINT',
                    x=Decimal(str(pt['x'])),
                    y=Decimal(str(pt['y'])),
                    z=Decimal(str(pt.get('z', 0.0)))
                )
                created_nodes.append(node)
                seg_nodes.append(node)

            # Link sequential path nodes on the segment
            for p_idx in range(len(seg_nodes) - 1):
                n1 = seg_nodes[p_idx]
                n2 = seg_nodes[p_idx + 1]
                
                dist = math.sqrt((float(n1.x)-float(n2.x))**2 + (float(n1.y)-float(n2.y))**2)
                
                n1.connections.append({"node_id": str(n2.id), "weight": dist})
                n1.save()
                
                n2.connections.append({"node_id": str(n1.id), "weight": dist})
                n2.save()

                # Edge models for pathfinding
                NavigationEdge.objects.create(
                    warehouse=warehouse,
                    from_node=n1,
                    to_node=n2,
                    edge_weight=Decimal(str(dist)),
                    dynamic_cost=Decimal(str(dist))
                )
                NavigationEdge.objects.create(
                    warehouse=warehouse,
                    from_node=n2,
                    to_node=n1,
                    edge_weight=Decimal(str(dist)),
                    dynamic_cost=Decimal(str(dist))
                )

        # Connect dock node to closest path node to ensure it's part of the routable graph
        path_nodes = [n for n in created_nodes if n.node_type == 'PATH_POINT']
        if path_nodes:
            closest_path_node = None
            min_dist = float('inf')
            dx, dy = float(dock_node.x), float(dock_node.y)
            for p_node in path_nodes:
                dist = math.sqrt((float(p_node.x) - dx)**2 + (float(p_node.y) - dy)**2)
                if dist < min_dist:
                    min_dist = dist
                    closest_path_node = p_node

            if closest_path_node:
                if not hasattr(dock_node, 'connections') or dock_node.connections is None:
                    dock_node.connections = []
                dock_node.connections.append({"node_id": str(closest_path_node.id), "weight": min_dist})
                dock_node.save()

                if not hasattr(closest_path_node, 'connections') or closest_path_node.connections is None:
                    closest_path_node.connections = []
                closest_path_node.connections.append({"node_id": str(dock_node.id), "weight": min_dist})
                closest_path_node.save()

                NavigationEdge.objects.create(
                    warehouse=warehouse,
                    from_node=dock_node,
                    to_node=closest_path_node,
                    edge_weight=Decimal(str(min_dist)),
                    dynamic_cost=Decimal(str(min_dist))
                )
                NavigationEdge.objects.create(
                    warehouse=warehouse,
                    from_node=closest_path_node,
                    to_node=dock_node,
                    edge_weight=Decimal(str(min_dist)),
                    dynamic_cost=Decimal(str(min_dist))
                )

        # 2. Add rack node access points & link them to the dock or nearest node
        racks = Rack.objects.filter(zone__warehouse=warehouse)
        for rack in racks:
            # Resolve access point
            rack_coord = rack.coordinates.first()
            if rack_coord:
                rx, ry, rz = float(rack_coord.access_point_x), float(rack_coord.access_point_y), float(rack_coord.access_point_z)
            else:
                rx, ry, rz = float(rack.x) + 1.0, float(rack.y) + 1.0, float(rack.z)
            
            node_name = f"PICK-NODE-{rack.rack_code}"
            # Delete if exists
            NavigationNode.objects.filter(warehouse=warehouse, node_name=node_name).delete()
            
            rack_node = NavigationNode.objects.create(
                warehouse=warehouse,
                node_name=node_name,
                node_type='PICK_POINT',
                x=Decimal(str(rx)),
                y=Decimal(str(ry)),
                z=Decimal(str(rz))
            )
            created_nodes.append(rack_node)

            # Connect this picking node to the closest node in our graph
            closest_node = None
            min_dist = float('inf')
            for n in created_nodes:
                if n.id == rack_node.id:
                    continue
                dist = math.sqrt((float(n.x) - rx)**2 + (float(n.y) - ry)**2)
                if dist < min_dist:
                    min_dist = dist
                    closest_node = n

            if closest_node:
                # Add connections
                rack_node.connections.append({"node_id": str(closest_node.id), "weight": min_dist})
                rack_node.save()

                closest_node.connections.append({"node_id": str(rack_node.id), "weight": min_dist})
                closest_node.save()

                # Save edges
                NavigationEdge.objects.create(
                    warehouse=warehouse,
                    from_node=rack_node,
                    to_node=closest_node,
                    edge_weight=Decimal(str(min_dist)),
                    dynamic_cost=Decimal(str(min_dist))
                )
                NavigationEdge.objects.create(
                    warehouse=warehouse,
                    from_node=closest_node,
                    to_node=rack_node,
                    edge_weight=Decimal(str(min_dist)),
                    dynamic_cost=Decimal(str(min_dist))
                )

        # 3. StorageLocationNodeMap generation
        bins = Bin.objects.filter(shelf__rack__zone__warehouse=warehouse)
        for b in bins:
            StorageLocationNodeMap.objects.filter(bin=b).delete()

            # Find nearest navigation node
            closest_node = None
            min_dist = float('inf')
            
            rack_obj = b.shelf.rack
            rack_coord = rack_obj.coordinates.first()
            if rack_coord:
                bx, by = float(rack_coord.access_point_x), float(rack_coord.access_point_y)
            else:
                bx, by = float(rack_obj.x), float(rack_obj.y)

            for n in created_nodes:
                dist = math.sqrt((float(n.x) - bx)**2 + (float(n.y) - by)**2)
                if dist < min_dist:
                    min_dist = dist
                    closest_node = n

            if closest_node:
                StorageLocationNodeMap.objects.create(
                    warehouse=warehouse,
                    bin=b,
                    navigation_node=closest_node
                )

        return created_nodes
