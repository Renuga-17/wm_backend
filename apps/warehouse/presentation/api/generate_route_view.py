from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.warehouse.infrastructure.persistence.models import Bin
from apps.warehouse.infrastructure.persistence.models import StorageLocationNodeMap
from apps.warehouse.presentation.api.serializers import GenerateRouteRequestSerializer
from apps.warehouse.application.services.pathfinding import PathfindingService

class GenerateRouteView(APIView):
    """POST /api/routes/generate/
    Exposes the existing routing engine.
    Request body:
        {
            "source_bin_id": "<uuid>",
            "destination_bin_id": "<uuid>"
        }
    """

    def post(self, request, *args, **kwargs):
        serializer = GenerateRouteRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        src_id = serializer.validated_data["source_bin_id"]
        dst_id = serializer.validated_data["destination_bin_id"]

        # Retrieve bins, 400 if not found
        try:
            src_bin = Bin.objects.get(id=src_id)
            dst_bin = Bin.objects.get(id=dst_id)
        except Bin.DoesNotExist:
            return Response({"error": "Invalid bin ID provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Mapping to navigation nodes, 404 if missing
        try:
            src_map = StorageLocationNodeMap.objects.get(bin=src_bin)
            dst_map = StorageLocationNodeMap.objects.get(bin=dst_bin)
        except StorageLocationNodeMap.DoesNotExist:
            return Response({"error": "StorageLocationNodeMap missing for provided bin(s)."}, status=status.HTTP_404_NOT_FOUND)

        src_node = src_map.navigation_node
        dst_node = dst_map.navigation_node
        warehouse_id = src_node.warehouse_id

        # Ensure both nodes belong to the same warehouse
        if dst_node.warehouse_id != warehouse_id:
            return Response({"error": "Source and destination belong to different warehouses."}, status=status.HTTP_400_BAD_REQUEST)

        distance, path_nodes = PathfindingService.a_star_search(warehouse_id, src_node, dst_node)
        if distance == float('inf'):
            return Response({"error": "No route found between the specified bins."}, status=status.HTTP_404_NOT_FOUND)

        path = [
            {
                "node_id": str(node.id),
                "node_name": node.node_name,
                "x": float(node.x),
                "y": float(node.y),
                "z": float(node.z),
            }
            for node in path_nodes
        ]

        return Response({
            "success": True,
            "distance": distance,
            "path": path,
        }, status=status.HTTP_200_OK)
