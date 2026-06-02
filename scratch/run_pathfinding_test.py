import sys
from apps.routes.services.pathfinding import PathfindingService
from apps.warehouses.models import NavigationNode, NavigationEdge

# Load all nodes
nodes = list(NavigationNode.objects.all())
if not nodes:
    print('No NavigationNode records found.')
    sys.exit(0)

# Choose a source node (first)
src = nodes[0]
warehouse_id = src.warehouse_id

# BFS to find reachable nodes via non-blocked edges
visited = set([str(src.id)])
frontier = [src]
while frontier:
    cur = frontier.pop()
    outgoing = NavigationEdge.objects.filter(from_node=cur, is_blocked=False)
    for edge in outgoing:
        nid = str(edge.to_node_id)
        if nid not in visited:
            visited.add(nid)
            frontier.append(edge.to_node)

# Determine a destination node that is reachable (different from source)
reachable_ids = visited - {str(src.id)}
if reachable_ids:
    dst_id = next(iter(reachable_ids))
    dst = NavigationNode.objects.get(id=dst_id)
    dist, path = PathfindingService.a_star_search(warehouse_id, src, dst)
    print('source', src.node_name)
    print('destination', dst.node_name)
    print('route found', bool(path))
    print('total distance', dist)
    print('node sequence', [n.node_name for n in path])
else:
    print('No other reachable node from source; graph may be disconnected.')

# Graph connectivity analysis
all_node_ids = set(str(n.id) for n in nodes)
unreachable = all_node_ids - visited
print('Total nodes', len(nodes))
print('Reachable from source', len(visited))
print('Unreachable nodes count', len(unreachable))
if unreachable:
    unreachable_nodes = NavigationNode.objects.filter(id__in=unreachable)
    print('Unreachable node names:', [n.node_name for n in unreachable_nodes])

# Isolated nodes (no in or out edges)
isolated = []
for n in nodes:
    has_out = NavigationEdge.objects.filter(from_node=n).exists()
    has_in = NavigationEdge.objects.filter(to_node=n).exists()
    if not has_out and not has_in:
        isolated.append(n.node_name)
print('Isolated nodes count', len(isolated))
if isolated:
    print('Isolated node names:', isolated)
