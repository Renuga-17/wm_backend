import logging
from django.utils import timezone
from apps.warehouse.infrastructure.persistence.models import Zone
from apps.warehouse.infrastructure.persistence.models import Bin
from integrations.clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)

class OperationalScoringEngine:
    @staticmethod
    def _get_ch_client():
        try:
            return ClickHouseClient()
        except Exception as e:
            logger.error(f"ClickHouse client error: {e}")
            return None

    @classmethod
    def calculate_operational_scores(cls, warehouse_id):
        """
        Computes four core warehouse intelligence indicators (Congestion, Efficiency, Utilization, Accessibility).
        Uses ClickHouse aggregate telemetry and PostgreSQL bin records.
        """
        ch = cls._get_ch_client()
        now = timezone.now()
        start_time = now - timezone.timedelta(hours=24)

        # 1. Congestion Score (from warehouse_heatmaps or route_analytics)
        congestion_val = 0.15  # Fallback
        if ch:
            query = """
                SELECT avg(congestion_level) 
                FROM route_analytics 
                WHERE route_time >= %(start_time)s
            """
            res = ch.execute_query(query, params={'start_time': start_time})
            if res and res.result_rows and res.result_rows[0][0] is not None:
                try:
                    val = float(res.result_rows[0][0])
                    import math
                    if not math.isnan(val):
                        congestion_val = val
                except ValueError:
                    pass
        
        # 2. Efficiency Score (based on picking times)
        # Average pick times in ClickHouse. If average pick time is e.g. 40 seconds,
        # score is higher. We define: Efficiency = 1.0 - (avg_pick_time_sec / 150.0)
        efficiency_val = 0.75  # Fallback
        if ch:
            query = """
                SELECT avg(avg_pick_time) 
                FROM warehouse_heatmaps 
                WHERE heatmap_time >= %(start_time)s
            """
            res = ch.execute_query(query, params={'start_time': start_time})
            if res and res.result_rows and res.result_rows[0][0] is not None:
                try:
                    val = float(res.result_rows[0][0])
                    import math
                    if not math.isnan(val):
                        efficiency_val = max(0.0, min(1.0, 1.0 - (val / 150.0)))
                except ValueError:
                    pass

        # 3. Utilization Score (from PG bin storage occupancy)
        total_bins = Bin.objects.filter(shelf__rack__zone__warehouse_id=warehouse_id).count()
        occupied_bins = Bin.objects.filter(shelf__rack__zone__warehouse_id=warehouse_id, is_occupied=True).count()
        utilization_val = occupied_bins / total_bins if total_bins > 0 else 0.0

        # 4. Accessibility Score (A* optimized route ratio)
        accessibility_val = 0.80  # Fallback
        if ch:
            query = """
                SELECT sum(optimized) * 1.0 / count() 
                FROM route_analytics 
                WHERE route_time >= %(start_time)s
            """
            res = ch.execute_query(query, params={'start_time': start_time})
            if res and res.result_rows and res.result_rows[0][0] is not None:
                try:
                    val = float(res.result_rows[0][0])
                    import math
                    if not math.isnan(val):
                        accessibility_val = val
                except ValueError:
                    pass

        return {
            "congestion_score": round(congestion_val, 4),
            "efficiency_score": round(efficiency_val, 4),
            "utilization_score": round(utilization_val, 4),
            "accessibility_score": round(accessibility_val, 4),
            "warehouse_id": str(warehouse_id),
            "calculated_at": timezone.now().isoformat()
        }
