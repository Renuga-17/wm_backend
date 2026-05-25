import math
import heapq
from apps.warehouses.models import NavigationNode, Rack, NavigationEdge

class PathfindingService:
    @staticmethod
    def _euclidean_distance(n1, n2):
        return math.sqrt(
            (float(n1.x) - float(n2.x))**2 + 
            (float(n1.y) - float(n2.y))**2 + 
            (float(n1.z) - float(n2.z))**2
        )

    @staticmethod
    def resolve_location_to_node(warehouse_id, location_string):
        """
        Resolves a string like 'DOCK_A' or 'RACK_A1' to the nearest NavigationNode.
        """
        # 1. Direct match with a NavigationNode
        node = NavigationNode.objects.filter(warehouse_id=warehouse_id, node_name=location_string).first()
        if node:
            return node
            
        # 2. Match with a Rack
        rack = Rack.objects.filter(zone__warehouse_id=warehouse_id, rack_code=location_string).first()
        if rack:
            # Find the closest navigation node to this rack
            nodes = NavigationNode.objects.filter(warehouse_id=warehouse_id)
            if not nodes.exists():
                raise ValueError(f"No navigation nodes found in warehouse {warehouse_id}")
                
            closest_node = None
            min_dist = float('inf')
            
            # Use rack coordinates or fallback to rack center
            rack_coords = rack.coordinates.first()
            if rack_coords:
                rx, ry, rz = float(rack_coords.access_point_x), float(rack_coords.access_point_y), float(rack_coords.access_point_z)
            else:
                rx, ry, rz = float(rack.x), float(rack.y), float(rack.z)
                
            for n in nodes:
                dist = math.sqrt((float(n.x) - rx)**2 + (float(n.y) - ry)**2 + (float(n.z) - rz)**2)
                if dist < min_dist:
                    min_dist = dist
                    closest_node = n
            
            if closest_node:
                return closest_node
                
        raise ValueError(f"Could not resolve location '{location_string}' to a routable node.")

    @staticmethod
    def get_graph(warehouse_id):
        """
        Builds the adjacency list from NavigationEdge objects (with dynamic weights and blocking).
        Auto-bootstraps NavigationEdge entries from NavigationNode.connections if none exist.
        Returns:
            nodes_map: dict of node_id -> NavigationNode object
            graph: dict of node_id -> list of (neighbor_id, cost)
        """
        # 1. Check if we need to bootstrap NavigationEdge objects
        edges_exist = NavigationEdge.objects.filter(warehouse_id=warehouse_id).exists()
        if not edges_exist:
            nodes = NavigationNode.objects.filter(warehouse_id=warehouse_id)
            nodes_map = {str(n.id): n for n in nodes}
            edges_to_create = []
            seen_edges = set()
            
            for n in nodes:
                for conn in n.connections:
                    if isinstance(conn, dict):
                        neighbor_id = str(conn.get('node_id'))
                        weight = conn.get('weight')
                    else:
                        neighbor_id = str(conn)
                        weight = None
                        
                    if neighbor_id in nodes_map:
                        neighbor = nodes_map[neighbor_id]
                        if weight is None:
                            weight = PathfindingService._euclidean_distance(n, neighbor)
                        
                        edge_key = (str(n.id), str(neighbor.id))
                        if edge_key not in seen_edges:
                            edges_to_create.append(
                                NavigationEdge(
                                    warehouse_id=warehouse_id,
                                    from_node=n,
                                    to_node=neighbor,
                                    edge_weight=weight,
                                    dynamic_cost=weight
                                )
                            )
                            seen_edges.add(edge_key)
            
            if edges_to_create:
                NavigationEdge.objects.bulk_create(edges_to_create, ignore_conflicts=True)

        # 2. Build map and graph
        nodes = NavigationNode.objects.filter(warehouse_id=warehouse_id)
        nodes_map = {str(n.id): n for n in nodes}
        graph = {str(n.id): [] for n in nodes}
        
        edges = NavigationEdge.objects.filter(warehouse_id=warehouse_id)
        for edge in edges:
            from_id = str(edge.from_node_id)
            to_id = str(edge.to_node_id)
            
            # Skip blocked edges completely
            if edge.is_blocked:
                continue
                
            if from_id in graph and to_id in nodes_map:
                graph[from_id].append((to_id, float(edge.dynamic_cost)))
                
        return nodes_map, graph


    @staticmethod
    def a_star_search(warehouse_id, start_node, end_node):
        """
        Finds the shortest path between start_node and end_node using A*.
        Returns (distance, path_nodes_list)
        """
        if start_node.id == end_node.id:
            return 0.0, [start_node]
            
        nodes_map, graph = PathfindingService.get_graph(warehouse_id)
        start_id = str(start_node.id)
        end_id = str(end_node.id)
        
        if start_id not in nodes_map or end_id not in nodes_map:
            raise ValueError("Start or end node not in graph.")
            
        # priority queue: (f_score, node_id)
        open_set = []
        heapq.heappush(open_set, (0, start_id))
        
        came_from = {}
        g_score = {nid: float('inf') for nid in nodes_map}
        g_score[start_id] = 0
        
        f_score = {nid: float('inf') for nid in nodes_map}
        f_score[start_id] = PathfindingService._euclidean_distance(start_node, end_node)
        
        while open_set:
            _, current_id = heapq.heappop(open_set)
            
            if current_id == end_id:
                # Reconstruct path
                path = []
                curr = current_id
                while curr in came_from:
                    path.append(nodes_map[curr])
                    curr = came_from[curr]
                path.append(start_node)
                path.reverse()
                return g_score[end_id], path
                
            for neighbor_id, cost in graph.get(current_id, []):
                tentative_g_score = g_score[current_id] + cost
                
                if tentative_g_score < g_score[neighbor_id]:
                    came_from[neighbor_id] = current_id
                    g_score[neighbor_id] = tentative_g_score
                    
                    h_score = PathfindingService._euclidean_distance(nodes_map[neighbor_id], end_node)
                    f_score[neighbor_id] = g_score[neighbor_id] + h_score
                    
                    # Add to open set if not already there (this is simplified)
                    heapq.heappush(open_set, (f_score[neighbor_id], neighbor_id))
                    
        # No path found
        return float('inf'), []

    @staticmethod
    def nearest_neighbor_tsp(warehouse_id, start_node, target_nodes):
        """
        Computes a multi-stop route starting at start_node and visiting all target_nodes
        using a greedy nearest-neighbor approach.
        Returns (total_distance, ordered_path_nodes)
        """
        total_distance = 0.0
        full_path = [start_node]
        
        current_node = start_node
        unvisited = list(target_nodes)
        
        while unvisited:
            best_next = None
            best_dist = float('inf')
            best_path_segment = []
            
            for candidate in unvisited:
                dist, path = PathfindingService.a_star_search(warehouse_id, current_node, candidate)
                if dist < best_dist:
                    best_dist = dist
                    best_next = candidate
                    best_path_segment = path
                    
            if not best_next or best_dist == float('inf'):
                raise ValueError("Cannot reach all targets from the start node.")
                
            # Add segment to full path (skip the first node of segment to avoid duplicates)
            if len(best_path_segment) > 1:
                full_path.extend(best_path_segment[1:])
            total_distance += best_dist
            
            current_node = best_next
            unvisited.remove(best_next)
            
        return total_distance, full_path
