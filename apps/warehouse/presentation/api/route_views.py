from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.warehouse.infrastructure.persistence.models import Warehouse
from apps.warehouse.infrastructure.persistence.models import OptimizedRoute, RouteSegment, RouteHistory
from .serializers import RouteOptimizeRequestSerializer, OptimizedRouteSerializer
from apps.warehouse.application.services.pathfinding import PathfindingService
import math

class RouteViewSet(viewsets.GenericViewSet):
    queryset = OptimizedRoute.objects.all()
    serializer_class = OptimizedRouteSerializer

    def get_serializer_class(self):
        if self.action in ['optimize', 'multi_pick']:
            return RouteOptimizeRequestSerializer
        return OptimizedRouteSerializer

    @action(detail=False, methods=['post'])
    def optimize(self, request):
        """
        POST /api/routes/optimize
        {
            "warehouse_id": "...",
            "start": "DOCK_A",
            "targets": ["RACK_A1"]
        }
        """
        serializer = RouteOptimizeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        warehouse_id = data['warehouse_id']
        start_str = data['start']
        targets = data['targets']
        
        try:
            start_node = PathfindingService.resolve_location_to_node(warehouse_id, start_str)
            end_node = PathfindingService.resolve_location_to_node(warehouse_id, targets[0])
            
            distance, path_nodes = PathfindingService.a_star_search(warehouse_id, start_node, end_node)
            
            if distance == float('inf'):
                return Response({"error": "No valid route found between the points."}, status=status.HTTP_404_NOT_FOUND)
                
            # Assume robot speed is 1.5 m/s
            estimated_time = int(distance / 1.5)
            
            route = OptimizedRoute.objects.create(
                warehouse_id=warehouse_id,
                start_location=start_str,
                distance=distance,
                estimated_time=estimated_time
            )
            
            segments = []
            for i, node in enumerate(path_nodes):
                segments.append(RouteSegment(
                    route=route,
                    segment_order=i,
                    x=node.x,
                    y=node.y,
                    z=node.z
                ))
            RouteSegment.objects.bulk_create(segments)
            
            RouteHistory.objects.create(route=route)
            
            resp_serializer = OptimizedRouteSerializer(route)
            return Response(resp_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='multi-pick')
    def multi_pick(self, request):
        """
        POST /api/routes/multi-pick
        {
            "warehouse_id": "...",
            "start": "DOCK_A",
            "targets": ["RACK_A1", "RACK_B4"]
        }
        """
        serializer = RouteOptimizeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        warehouse_id = data['warehouse_id']
        start_str = data['start']
        targets = data['targets']
        
        try:
            start_node = PathfindingService.resolve_location_to_node(warehouse_id, start_str)
            target_nodes = []
            for t in targets:
                target_nodes.append(PathfindingService.resolve_location_to_node(warehouse_id, t))
                
            distance, path_nodes = PathfindingService.nearest_neighbor_tsp(warehouse_id, start_node, target_nodes)
            
            estimated_time = int(distance / 1.5)
            
            route = OptimizedRoute.objects.create(
                warehouse_id=warehouse_id,
                start_location=start_str,
                distance=distance,
                estimated_time=estimated_time
            )
            
            segments = []
            for i, node in enumerate(path_nodes):
                segments.append(RouteSegment(
                    route=route,
                    segment_order=i,
                    x=node.x,
                    y=node.y,
                    z=node.z
                ))
            RouteSegment.objects.bulk_create(segments)
            
            RouteHistory.objects.create(route=route)
            
            resp_serializer = OptimizedRouteSerializer(route)
            return Response(resp_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """GET /api/routes/:id"""
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def congestion(self, request):
        """
        GET /api/routes/congestion/?warehouse_id=...
        Returns all navigation edges for the given warehouse, with their congestion_score,
        is_blocked, dynamic_cost, etc.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        if not warehouse_id:
            return Response({"error": "warehouse_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Bootstrap if necessary
            PathfindingService.get_graph(warehouse_id)
        except Exception as e:
            return Response({"error": f"Failed to load or bootstrap graph: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            
        from apps.warehouse.infrastructure.persistence.models import NavigationEdge
        from apps.warehouse.presentation.api.serializers import NavigationEdgeSerializer
        
        edges = NavigationEdge.objects.filter(warehouse_id=warehouse_id).select_related('from_node', 'to_node')
        serializer = NavigationEdgeSerializer(edges, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='block-path')
    def block_path(self, request):
        """
        POST /api/routes/block-path/
        {
            "warehouse_id": "...",
            "from_node_id": "...",
            "to_node_id": "...",
            "is_blocked": true/false (optional),
            "congestion_score": float (optional),
            "travel_time": float (optional)
        }
        """
        warehouse_id = request.data.get('warehouse_id')
        from_node_id = request.data.get('from_node_id')
        to_node_id = request.data.get('to_node_id')
        
        if not all([warehouse_id, from_node_id, to_node_id]):
            return Response({"error": "warehouse_id, from_node_id, and to_node_id are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Bootstrap if necessary
        try:
            PathfindingService.get_graph(warehouse_id)
        except Exception as e:
            return Response({"error": f"Failed to load or bootstrap graph: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            
        from apps.warehouse.infrastructure.persistence.models import NavigationEdge
        from apps.warehouse.presentation.api.serializers import NavigationEdgeSerializer
        
        # Target the exact directed edge
        edge = NavigationEdge.objects.filter(warehouse_id=warehouse_id, from_node_id=from_node_id, to_node_id=to_node_id).first()
        if not edge:
            return Response({"error": "Navigation edge not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if 'is_blocked' in request.data:
            edge.is_blocked = bool(request.data['is_blocked'])
        if 'congestion_score' in request.data:
            edge.congestion_score = float(request.data['congestion_score'])
        if 'travel_time' in request.data:
            edge.travel_time = float(request.data['travel_time'])
            
        edge.save()
        
        # Mirror change on reciprocal edge if it exists (for bidirectional aisle blocking)
        reciprocal_edge = NavigationEdge.objects.filter(warehouse_id=warehouse_id, from_node_id=to_node_id, to_node_id=from_node_id).first()
        if reciprocal_edge:
            if 'is_blocked' in request.data:
                reciprocal_edge.is_blocked = bool(request.data['is_blocked'])
            if 'congestion_score' in request.data:
                reciprocal_edge.congestion_score = float(request.data['congestion_score'])
            if 'travel_time' in request.data:
                reciprocal_edge.travel_time = float(request.data['travel_time'])
            reciprocal_edge.save()
            
        # Broadcast real-time event to WebSockets
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    "routes",
                    {
                        "type": "route_update",
                        "event": "edge_updated",
                        "data": {
                            "from_node_id": from_node_id,
                            "to_node_id": to_node_id,
                            "is_blocked": edge.is_blocked,
                            "congestion_score": float(edge.congestion_score),
                            "travel_time": float(edge.travel_time),
                            "dynamic_cost": float(edge.dynamic_cost)
                        }
                    }
                )
        except Exception:
            pass
            
        serializer = NavigationEdgeSerializer(edge)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        """
        POST /api/routes/recalculate/
        {
            "route_id": "..."
        }
        """
        route_id = request.data.get('route_id')
        if not route_id:
            return Response({"error": "route_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            route = OptimizedRoute.objects.get(id=route_id)
        except OptimizedRoute.DoesNotExist:
            return Response({"error": "Route not found."}, status=status.HTTP_404_NOT_FOUND)
            
        segments = route.segments.all().order_by('segment_order')
        if not segments.exists():
            return Response({"error": "Route has no segments to recalculate."}, status=status.HTTP_400_BAD_REQUEST)
            
        warehouse_id = route.warehouse_id
        start_str = route.start_location
        
        try:
            from apps.warehouse.infrastructure.persistence.models import NavigationNode
            start_node = PathfindingService.resolve_location_to_node(warehouse_id, start_str)
            
            # Find the closest navigation node to the last segment's coordinates
            last_seg = segments.last()
            nodes = NavigationNode.objects.filter(warehouse_id=warehouse_id)
            end_node = None
            min_dist = float('inf')
            for n in nodes:
                dist = math.sqrt((float(n.x) - float(last_seg.x))**2 + (float(n.y) - float(last_seg.y))**2)
                if dist < min_dist:
                    min_dist = dist
                    end_node = n
                    
            if not end_node:
                return Response({"error": "Could not resolve destination node for recalculation."}, status=status.HTTP_400_BAD_REQUEST)
                
            distance, path_nodes = PathfindingService.a_star_search(warehouse_id, start_node, end_node)
            
            if distance == float('inf'):
                return Response({"error": "No valid operational route found under current congestion/blocking conditions."}, status=status.HTTP_404_NOT_FOUND)
                
            estimated_time = int(distance / 1.5)
            route.distance = distance
            route.estimated_time = estimated_time
            route.save()
            
            route.segments.all().delete()
            
            new_segments = []
            for i, node in enumerate(path_nodes):
                new_segments.append(RouteSegment(
                    route=route,
                    segment_order=i,
                    x=node.x,
                    y=node.y,
                    z=node.z
                ))
            RouteSegment.objects.bulk_create(new_segments)
            
            # Broadcast the recalculation update to the websocket group
            try:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        "routes",
                        {
                            "type": "route_update",
                            "event": "route_recalculated",
                            "data": {
                                "route_id": str(route.id),
                                "distance": float(route.distance),
                                "estimated_time": route.estimated_time,
                                "path": [[float(s.x), float(s.y)] for s in new_segments]
                            }
                        }
                    )
            except Exception:
                pass
                
            resp_serializer = OptimizedRouteSerializer(route)
            return Response(resp_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"Recalculation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

