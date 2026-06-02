import math
from django.core.management.base import BaseCommand
from apps.warehouses.models import NavigationNode, NavigationEdge


def euclidean_distance(n1, n2):
    return math.sqrt(
        (float(n1.x) - float(n2.x)) ** 2 +
        (float(n1.y) - float(n2.y)) ** 2 +
        (float(n1.z) - float(n2.z)) ** 2
    )


class Command(BaseCommand):
    help = "Generate NavigationEdge records connecting each NavigationNode to its seven nearest neighbours"

    def handle(self, *args, **options):
        nodes = list(NavigationNode.objects.all())
        total_nodes = len(nodes)
        created_count = 0
        skipped_count = 0

        # Pre‑compute distances for each node to avoid repeated DB hits
        for i, node in enumerate(nodes):
            # Compute distances to all other nodes
            distances = []
            for j, other in enumerate(nodes):
                if i == j:
                    continue  # skip self
                dist = euclidean_distance(node, other)
                distances.append((dist, other))
            # Sort and take the seven closest
            distances.sort(key=lambda x: x[0])
            nearest_seven = distances[:7]

            for dist, neighbor in nearest_seven:
                # Use get_or_create to avoid duplicate edges (directed)
                edge, created = NavigationEdge.objects.get_or_create(
                    warehouse=node.warehouse,
                    from_node=node,
                    to_node=neighbor,
                    defaults={
                        "edge_weight": dist,
                    },
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(
            f"Nodes processed: {total_nodes} | Edges created: {created_count} | Edges skipped: {skipped_count}"
        )
