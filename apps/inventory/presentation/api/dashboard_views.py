from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.inventory.infrastructure.persistence.models import Dashboard, RobotTask, RouteOptimization
from .serializers import DashboardSerializer, RobotTaskSerializer, RouteOptimizationSerializer
from apps.inventory.application.services.analytics_service import WarehouseAnalyticsService

class DashboardViewSet(viewsets.ModelViewSet):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer

class RobotTaskViewSet(viewsets.ModelViewSet):
    queryset = RobotTask.objects.all()
    serializer_class = RobotTaskSerializer

class RouteOptimizationViewSet(viewsets.ModelViewSet):
    queryset = RouteOptimization.objects.all()
    serializer_class = RouteOptimizationSerializer

class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for fetching warehouse ClickHouse analytics.
    """
    @action(detail=False, methods=['get'])
    def heatmaps(self, request):
        warehouse_id = request.query_params.get('warehouse_id')
        if not warehouse_id:
            return Response({"error": "warehouse_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        
        data = WarehouseAnalyticsService.get_spatial_heatmap(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def routes(self, request):
        warehouse_id = request.query_params.get('warehouse_id')
        if not warehouse_id:
            return Response({"error": "warehouse_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        
        data = WarehouseAnalyticsService.get_route_efficiency(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def telemetry(self, request):
        warehouse_id = request.query_params.get('warehouse_id')
        if not warehouse_id:
            return Response({"error": "warehouse_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        
        data = WarehouseAnalyticsService.get_sensor_telemetry_summary(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def throughput(self, request):
        warehouse_id = request.query_params.get('warehouse_id')
        if not warehouse_id:
            return Response({"error": "warehouse_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        
        data = WarehouseAnalyticsService.get_inventory_throughput(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

