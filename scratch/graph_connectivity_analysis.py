import os, sys
from collections import defaultdict, deque

# Set up Django environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.warehouse.infrastructure.persistence.models import NavigationNode, NavigationEdge

# Load nodes
nodes = list(NavigationNode.objects.all())
node_by_id = {str(n.id): n for n in nodes}

# Load existing directed edges (unblocked only)
edges = list(NavigationEdge.objects.filter(is_blocked=False))

# Build adjacency for undirected connectivity (ignore direction)
undirected_adj = defaultdict(set)
for e in edges:
    src = str(e.from_node_id)
    dst = str(e.to_node_id)
    undirected_adj[src].add(dst)
    undirected_adj[dst].add(src)

# Helper to find weakly connected components using BFS on undirected graph
visited = set()
components = []
for nid in node_by_id.keys():
    if nid in visited:
        continue
    comp = []
    queue = deque([nid])
    while queue:
        cur = queue.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        comp.append(cur)
        for nb in undirected_adj.get(cur, []):
            if nb not in visited:
                queue.append(nb)
    components.append(comp)

# Report component sizes
component_sizes = [len(c) for c in components]
largest_size = max(component_sizes) if component_sizes else 0
smallest_size = min(component_sizes) if component_sizes else 0
largest_idx = component_sizes.index(largest_size) if component_sizes else -1
smallest_idx = component_sizes.index(smallest_size) if component_sizes else -1

print('=== Weakly Connected Components Summary ===')
print(f'Number of components: {len(components)}')
print(f'Largest component size: {largest_size}')
print(f'Smallest component size: {smallest_size}')

for idx, comp in enumerate(components):
    names = [node_by_id[nid].node_name for nid in comp]
    print(f'Component {idx+1} (size {len(comp)}): {", ".join(names)}')

# Analyze why 3-nearest-neighbor strategy failed
# Compute average degree and max distance gaps
degrees = defaultdict(int)
for e in edges:
    degrees[str(e.from_node_id)] += 1
avg_degree = sum(degrees.values()) / len(nodes) if nodes else 0
print('\n=== Edge Statistics (directed) ===')
print(f'Total edges: {len(edges)}')
print(f'Average out-degree per node: {avg_degree:.2f}')

# Simulate higher neighbor strategies (5 and 7 nearest) without altering DB
# Precompute distances between all node pairs
def euclidean(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5

# Build distance matrix (list of tuples per node)
all_distances = {}
for n in nodes:
    dlist = []
    for m in nodes:
        if n.id == m.id:
            continue
        d = euclidean(n, m)
        dlist.append((str(m.id), d))
    dlist.sort(key=lambda x: x[1])
    all_distances[str(n.id)] = dlist

def simulate(k):
    # Simulate adding edges from each node to its k nearest neighbors (directed)
    new_edges = set()
    for src_id, dlist in all_distances.items():
        for neighbor_id, _ in dlist[:k]:
            new_edges.add((src_id, neighbor_id))
    # Combine with existing edges
    existing = {(str(e.from_node_id), str(e.to_node_id)) for e in edges}
    combined = existing.union(new_edges)
    # Compute weakly connected components on combined graph
    adj = defaultdict(set)
    for src, dst in combined:
        adj[src].add(dst)
        adj[dst].add(src)
    visited2 = set()
    comps = []
    for nid in node_by_id.keys():
        if nid in visited2:
            continue
        comp = []
        q = deque([nid])
        while q:
            cur = q.popleft()
            if cur in visited2:
                continue
            visited2.add(cur)
            comp.append(cur)
            for nb in adj.get(cur, []):
                if nb not in visited2:
                    q.append(nb)
        comps.append(comp)
    return len(combined), len(comps), [len(c) for c in comps]

for k in (5, 7):
    edge_cnt, comp_cnt, comp_sizes = simulate(k)
    print(f'\n--- Simulation with {k}-nearest neighbors ---')
    print(f'Resulting edge count (directed): {edge_cnt}')
    print(f'Number of weakly connected components: {comp_cnt}')
    print(f'Component sizes: {comp_sizes}')

# Recommendations will be made based on these observations (not printed here).
