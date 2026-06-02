import sys
from django.core.management.base import BaseCommand
from apps.routes.services.pathfinding import PathfindingService
from apps.warehouses.models import NavigationNode, NavigationEdge
from collections import deque

class Command(BaseCommand):
    help = 'Verifies the health of the route engine by analyzing the navigation graph and performing a sample pathfinding test.'

    def handle(self, *args, **options):
        # Fetch all navigation nodes
        nodes = list(NavigationNode.objects.all())
        if len(nodes) < 2:
            self.stdout.write(self.style.ERROR('Not enough NavigationNode records to perform analysis.'))
            return

        # Assume single warehouse; use the warehouse of the first node
        warehouse_id = nodes[0].warehouse_id
        total_nodes = NavigationNode.objects.filter(warehouse_id=warehouse_id).count()
        total_edges = NavigationEdge.objects.filter(warehouse_id=warehouse_id, is_blocked=False).count()
        self.stdout.write(f'Total NavigationNode count: {total_nodes}')
        self.stdout.write(f'Total NavigationEdge count (unblocked): {total_edges}')

        # Build adjacency list for BFS/DFS
        adj = {}
        for edge in NavigationEdge.objects.filter(warehouse_id=warehouse_id, is_blocked=False):
            adj.setdefault(str(edge.from_node_id), set()).add(str(edge.to_node_id))
            # Assuming undirected for reachability? If directed, also consider reverse if needed
            # For reachability from source we follow outgoing edges only

        # Perform BFS from first node to find reachable nodes
        src_node = nodes[0]
        visited = set()
        queue = deque([str(src_node.id)])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        reachable_count = len(visited)
        self.stdout.write(f'Reachable nodes from source "{src_node.node_name}": {reachable_count} out of {total_nodes}')

        # Identify isolated nodes (no incoming and no outgoing edges)
        isolated_nodes = []
        for node in NavigationNode.objects.filter(warehouse_id=warehouse_id):
            has_out = NavigationEdge.objects.filter(from_node=node, is_blocked=False).exists()
            has_in = NavigationEdge.objects.filter(to_node=node, is_blocked=False).exists()
            if not has_out and not has_in:
                isolated_nodes.append(node.node_name)
        self.stdout.write(f'Isolated nodes count: {len(isolated_nodes)}')
        if isolated_nodes:
            self.stdout.write('Isolated node names: ' + ', '.join(isolated_nodes))

        # Sample pathfinding between first and last node
        dst_node = nodes[-1]
        try:
            distance, path = PathfindingService.a_star_search(warehouse_id, src_node, dst_node)
            found = bool(path)
            path_names = [n.node_name for n in path] if path else []
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during pathfinding: {e}'))
            return

        self.stdout.write('\nSample Pathfinding Test:')
        self.stdout.write(f'  Source: {src_node.node_name}')
        self.stdout.write(f'  Destination: {dst_node.node_name}')
        self.stdout.write(f'  Route found: {found}')
        self.stdout.write(f'  Total distance: {distance}')
        self.stdout.write(f'  Node sequence: {" -> ".join(path_names)}')
