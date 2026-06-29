from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Count, Q
from apps.warehouse.infrastructure.persistence.models import WarehouseLayout, Rack, SpatialEntity, WarehousePath, NavigationNode, NavigationEdge, Warehouse
from apps.warehouse.infrastructure.persistence.models import Zone
from apps.warehouse.infrastructure.persistence.models import Bin
from .layout_serializers import WarehouseLayoutSerializer
from .serializers import SpatialEntitySerializer, WarehousePathSerializer, NavigationNodeSerializer
from .twin_serializers import TwinRackSerializer, TwinZoneSerializer
from common.permissions import ReadOnlyOrAuthenticated
import logging

logger = logging.getLogger(__name__)


class WarehouseTwinDetailView(APIView):
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(self, request, layout_id):
        try:
            layout = WarehouseLayout.objects.get(id=layout_id)
        except WarehouseLayout.DoesNotExist:
            return Response({"error": "Warehouse layout not found"}, status=status.HTTP_404_NOT_FOUND)

        warehouse = layout.warehouse

        # Query spatial structures with prefetching to avoid N+1 queries
        zones = Zone.objects.filter(warehouse=warehouse).prefetch_related('boundaries').order_by('id')
        racks = Rack.objects.filter(zone__warehouse=warehouse).prefetch_related('shelves__bins').order_by('id')
        entities = SpatialEntity.objects.filter(warehouse=warehouse).order_by('id')
        paths = WarehousePath.objects.filter(warehouse=warehouse).order_by('id')
        nodes = NavigationNode.objects.filter(warehouse=warehouse).order_by('id')

        # Compile consolidated digital twin
        payload = {
            "layout": WarehouseLayoutSerializer(layout).data,
            "zones": TwinZoneSerializer(zones, many=True).data,
            "racks": TwinRackSerializer(racks, many=True).data,
            "spatial_entities": SpatialEntitySerializer(entities, many=True).data,
            "paths": WarehousePathSerializer(paths, many=True).data,
            "navigation_nodes": NavigationNodeSerializer(nodes, many=True).data
        }
        return Response(payload, status=status.HTTP_200_OK)


class TwinRacksView(APIView):
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(self, request):
        # Prefetch shelves and bins nested relationship to avoid N+1 queries during serialization
        racks = Rack.objects.all().prefetch_related('shelves__bins').order_by('id')
        return Response(TwinRackSerializer(racks, many=True).data, status=status.HTTP_200_OK)


class TwinZonesView(APIView):
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(self, request):
        # Prefetch boundaries to avoid N+1 queries during serialization
        zones = Zone.objects.all().prefetch_related('boundaries').order_by('id')
        return Response(TwinZoneSerializer(zones, many=True).data, status=status.HTTP_200_OK)


class TwinOccupancyView(APIView):
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(self, request):
        # Calculate overall WMS occupancy metrics
        total_bins = Bin.objects.count()
        occupied_bins = Bin.objects.filter(is_occupied=True).count()
        occupancy_percentage = (occupied_bins / total_bins * 100.0) if total_bins > 0 else 0.0

        # Calculate per-rack occupancy metrics using annotated SQL to avoid N+1 loop count queries
        racks = Rack.objects.annotate(
            total_bins_count=Count('shelves__bins'),
            occupied_bins_count=Count('shelves__bins', filter=Q(shelves__bins__is_occupied=True))
        ).order_by('id')
        rack_stats = []

        for rack in racks:
            rack_total = rack.total_bins_count
            rack_occupied = rack.occupied_bins_count
            rack_pct = (rack_occupied / rack_total * 100.0) if rack_total > 0 else 0.0

            rack_stats.append({
                "rack_id": str(rack.id),
                "rack_code": rack.rack_code,
                "total_bins": rack_total,
                "occupied_bins": rack_occupied,
                "occupancy_percentage": round(rack_pct, 2)
            })

        payload = {
            "overall": {
                "total_bins": total_bins,
                "occupied_bins": occupied_bins,
                "occupancy_percentage": round(occupancy_percentage, 2)
            },
            "racks": rack_stats
        }
        return Response(payload, status=status.HTTP_200_OK)


class TwinPathsView(APIView):
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(self, request):
        try:
            paths = WarehousePath.objects.all().order_by('id')
            nodes = NavigationNode.objects.all().order_by('id')
            if not paths:
                # Build a graph using NetworkX for dynamic path generation
                import networkx as nx
                G = nx.DiGraph()
                # Add nodes with their IDs
                for node in nodes:
                    G.add_node(str(node.id), x=float(node.x), y=float(node.y), z=float(node.z))
                # Add edges with weight (distance)
                for edge in NavigationEdge.objects.filter(warehouse=nodes.first().warehouse).select_related('from_node', 'to_node'):
                    G.add_edge(str(edge.from_node.id), str(edge.to_node.id), weight=float(edge.edge_weight))
                # Compute all-pairs shortest paths (fallback when no stored paths)
                fallback_paths = []
                for source in G.nodes:
                    lengths, paths_dict = nx.single_source_dijkstra(G, source, weight='weight')
                    for target, distance in lengths.items():
                        if source == target:
                            continue
                        fallback_paths.append({
                            "source": source,
                            "target": target,
                            "path_nodes": paths_dict[target],
                            "total_distance": distance,
                        })
                serializer_data = fallback_paths
            else:
                serializer_data = WarehousePathSerializer(paths, many=True).data
            payload = {
                "paths": serializer_data,
                "navigation_nodes": NavigationNodeSerializer(nodes, many=True).data
            }
            return Response(payload, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Error retrieving twin paths")
            return Response({"error": "Unable to retrieve paths"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from .summary_serializers import TwinSummarySerializer


class TwinSummaryView(APIView):
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(self, request):
        total_warehouses = Warehouse.objects.count()
        total_zones = Zone.objects.count()
        total_racks = Rack.objects.count()
        total_bins = Bin.objects.count()
        occupied_bins = Bin.objects.filter(is_occupied=True).count()
        occupancy_percentage = (occupied_bins / total_bins * 100.0) if total_bins > 0 else 0.0
        navigation_node_count = NavigationNode.objects.count()
        navigation_edge_count = NavigationEdge.objects.count()
        data = {
            "total_warehouses": total_warehouses,
            "total_zones": total_zones,
            "total_racks": total_racks,
            "total_bins": total_bins,
            "occupancy_percentage": round(occupancy_percentage, 2),
            "navigation_node_count": navigation_node_count,
            "navigation_edge_count": navigation_edge_count,
        }
        serializer = TwinSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
