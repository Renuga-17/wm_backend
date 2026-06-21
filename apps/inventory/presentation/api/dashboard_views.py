from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
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
    ViewSet for fetching warehouse ClickHouse analytics and heatmaps.
    All endpoints accept warehouse_id, start_time, end_time query params.
    """
    permission_classes = [AllowAny]

    # ------------------------------------------------------------------
    # Helper to extract common query params
    # ------------------------------------------------------------------

    def _get_params(self, request):
        warehouse_id = request.query_params.get('warehouse_id')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        return warehouse_id, start_time, end_time

    def _require_warehouse(self, request):
        warehouse_id, start_time, end_time = self._get_params(request)
        if not warehouse_id:
            return None, None, None, Response(
                {"error": "warehouse_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return warehouse_id, start_time, end_time, None

    # ------------------------------------------------------------------
    # EXISTING ENDPOINTS (preserved)
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'])
    def heatmaps(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_spatial_heatmap(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def routes(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_route_efficiency(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def telemetry(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_sensor_telemetry_summary(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def throughput(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_inventory_throughput(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # NEW ANALYTICS ENDPOINTS
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='warehouse-kpis')
    def warehouse_kpis(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_warehouse_kpis(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='occupancy-trends')
    def occupancy_trends(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_occupancy_trends(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='inventory-movements')
    def inventory_movements(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_inventory_movements(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='inbound-metrics')
    def inbound_metrics(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_inbound_metrics(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='outbound-metrics')
    def outbound_metrics(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_outbound_metrics(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='recommendation-metrics')
    def recommendation_metrics(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_recommendation_metrics(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='route-metrics')
    def route_metrics(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_route_metrics(warehouse_id, start_time, end_time)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='top-zones')
    def top_zones(self, request):
        warehouse_id, start_time, end_time, err = self._require_warehouse(request)
        if err:
            return err

        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10

        data = WarehouseAnalyticsService.get_top_zones(warehouse_id, start_time, end_time, limit=limit)
        return Response(data, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # HEATMAP ENDPOINTS
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='zone-heatmap')
    def zone_heatmap(self, request):
        warehouse_id, _, _, err = self._require_warehouse(request)
        if err:
            return err

        data = WarehouseAnalyticsService.get_zone_heatmap(warehouse_id)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='rack-heatmap')
    def rack_heatmap(self, request):
        warehouse_id, _, _, err = self._require_warehouse(request)
        if err:
            return err

        zone_id = request.query_params.get('zone_id')
        data = WarehouseAnalyticsService.get_rack_heatmap(warehouse_id, zone_id=zone_id)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='bin-heatmap')
    def bin_heatmap(self, request):
        warehouse_id, _, _, err = self._require_warehouse(request)
        if err:
            return err

        zone_id = request.query_params.get('zone_id')
        rack_id = request.query_params.get('rack_id')
        data = WarehouseAnalyticsService.get_bin_utilization_heatmap(
            warehouse_id, zone_id=zone_id, rack_id=rack_id
        )
        return Response(data, status=status.HTTP_200_OK)
