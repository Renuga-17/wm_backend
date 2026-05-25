from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Count, Q
from .models import WarehouseLayout, Rack, SpatialEntity, WarehousePath, NavigationNode
from apps.zones.models import Zone
from apps.bins.models import Bin
from .layout_serializers import WarehouseLayoutSerializer
from .serializers import SpatialEntitySerializer, WarehousePathSerializer, NavigationNodeSerializer
from .twin_serializers import TwinRackSerializer, TwinZoneSerializer
import logging

logger = logging.getLogger(__name__)

class WarehouseTwinDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, layout_id):
        try:
            layout = WarehouseLayout.objects.get(id=layout_id)
        except WarehouseLayout.DoesNotExist:
            return Response({"error": "Warehouse layout not found"}, status=status.HTTP_404_NOT_FOUND)

        warehouse = layout.warehouse
        
        # Query spatial structures
        zones = Zone.objects.filter(warehouse=warehouse).order_by('id')
        racks = Rack.objects.filter(zone__warehouse=warehouse).order_by('id')
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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        racks = Rack.objects.all().order_by('id')
        return Response(TwinRackSerializer(racks, many=True).data, status=status.HTTP_200_OK)


class TwinZonesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        zones = Zone.objects.all().order_by('id')
        return Response(TwinZoneSerializer(zones, many=True).data, status=status.HTTP_200_OK)


class TwinOccupancyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Calculate overall WMS occupancy metrics
        total_bins = Bin.objects.count()
        occupied_bins = Bin.objects.filter(is_occupied=True).count()
        occupancy_percentage = (occupied_bins / total_bins * 100.0) if total_bins > 0 else 0.0

        # Calculate per-rack occupancy metrics
        racks = Rack.objects.all().order_by('id')
        rack_stats = []
        
        for rack in racks:
            # Query bins belonging to this rack
            rack_bins = Bin.objects.filter(shelf__rack=rack)
            rack_total = rack_bins.count()
            rack_occupied = rack_bins.filter(is_occupied=True).count()
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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        paths = WarehousePath.objects.all().order_by('id')
        nodes = NavigationNode.objects.all().order_by('id')
        
        payload = {
            "paths": WarehousePathSerializer(paths, many=True).data,
            "navigation_nodes": NavigationNodeSerializer(nodes, many=True).data
        }
        return Response(payload, status=status.HTTP_200_OK)
