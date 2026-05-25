import logging
from decimal import Decimal
from django.utils import timezone
from apps.zones.models import Zone
from apps.bins.models import Bin
from apps.recommendations.models import SystemAlert
from integrations.clickhouse_client import ClickHouseClient
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

class HotspotPreventionEngine:
    @staticmethod
    def _get_ch_client():
        try:
            return ClickHouseClient()
        except Exception as e:
            logger.error(f"ClickHouse client error: {e}")
            return None

    @classmethod
    def analyze_hotspots(cls, warehouse_id):
        """
        Analyzes live zone telemetry, route congestion, and occupancy stats.
        Generates SystemAlert instances and lists zone hotspot risk scores.
        """
        zones = Zone.objects.filter(warehouse_id=warehouse_id)
        results = []
        ch = cls._get_ch_client()
        channel_layer = get_channel_layer()

        # Time threshold for live metrics (past 2 hours)
        now = timezone.now()
        start_time = now - timezone.timedelta(hours=2)

        for zone in zones:
            zname = zone.zone_name
            ztype = zone.zone_type

            # 1. Gather PG occupancy metrics
            total_bins = Bin.objects.filter(shelf__rack__zone=zone).count()
            occupied_bins = Bin.objects.filter(shelf__rack__zone=zone, is_occupied=True).count()
            occupancy_ratio = occupied_bins / total_bins if total_bins > 0 else 0.0

            # 2. Gather ClickHouse metrics if available
            ch_congestion = 0.0
            temp_warning = False
            
            if ch:
                # Query recent congestion score
                cong_query = """
                    SELECT round(avg(congestion_score), 4)
                    FROM warehouse_heatmaps
                    WHERE zone_code = %(zone_code)s AND heatmap_time >= %(start_time)s
                """
                params = {'zone_code': zname, 'start_time': start_time}
                cong_res = ch.execute_query(cong_query, params=params)
                if cong_res and cong_res.result_rows and cong_res.result_rows[0][0] is not None:
                    try:
                        val = float(cong_res.result_rows[0][0])
                        import math
                        if not math.isnan(val):
                            ch_congestion = val
                    except ValueError:
                        pass

                # Query sensor status warnings
                sensor_query = """
                    SELECT count() 
                    FROM sensor_events 
                    WHERE zone_code = %(zone_code)s 
                      AND event_time >= %(start_time)s 
                      AND status = 'WARNING'
                """
                sensor_res = ch.execute_query(sensor_query, params=params)
                if sensor_res and sensor_res.result_rows and sensor_res.result_rows[0][0] > 0:
                    temp_warning = True

            # 3. Calculate dynamic risk score (blend occupancy, congestion, sensor warnings)
            risk_score = 0.3 * occupancy_ratio + 0.5 * ch_congestion
            if temp_warning:
                risk_score += 0.2
            
            risk_score = min(max(risk_score, 0.0), 1.0)

            # 4. Formulate recommendations & severity
            recommendation = "Zone operating within normal parameters."
            severity = "INFO"

            if risk_score >= 0.75:
                severity = "CRITICAL"
                if occupancy_ratio > 0.85:
                    recommendation = f"Zone {zname} is severely overutilized ({round(occupancy_ratio*100, 1)}% occupancy). Bulk-trigger re-slotting of slow-moving items."
                else:
                    recommendation = f"Severe traffic bottleneck detected in Zone {zname}. Reroute active picker AGVs to alternative corridors."
            elif risk_score >= 0.50:
                severity = "WARNING"
                if temp_warning:
                    recommendation = f"Thermal threshold exceeded in cold storage Zone {zname}. Audit cooling system ventilation."
                else:
                    recommendation = f"Zone {zname} congestion is rising. Redistribute fast-moving product arrivals."

            # 5. Generate DB Alert if severity is high (deduplicated by zone in past 30 mins)
            alert = None
            if severity in ["WARNING", "CRITICAL"]:
                recent_alert_exists = SystemAlert.objects.filter(
                    alert_type="CONGESTION" if severity == "WARNING" else "OVERUTILIZED_RACK",
                    zone_code=zname,
                    is_resolved=False,
                    created_at__gte=now - timezone.timedelta(minutes=30)
                ).exists()

                if not recent_alert_exists:
                    alert = SystemAlert.objects.create(
                        alert_type="CONGESTION" if severity == "WARNING" else "OVERUTILIZED_RACK",
                        zone_code=zname,
                        severity=severity,
                        message=recommendation
                    )

                    # Broadcast WS Alert
                    if channel_layer:
                        try:
                            # 1. Broadcast to general alerts group
                            async_to_sync(channel_layer.group_send)(
                                "system_alerts",
                                {
                                    "type": "alert_message",
                                    "event": "new_alert",
                                    "data": {
                                        "alert_id": str(alert.id),
                                        "alert_type": alert.alert_type,
                                        "zone_code": zname,
                                        "severity": severity,
                                        "message": recommendation,
                                        "created_at": alert.created_at.isoformat()
                                    }
                                }
                            )
                            # 2. Broadcast to congestion alerts group
                            async_to_sync(channel_layer.group_send)(
                                "congestion_alerts",
                                {
                                    "type": "congestion_message",
                                    "event": "congestion_update",
                                    "data": {
                                        "zone": zname,
                                        "risk_score": round(risk_score, 4),
                                        "severity": severity,
                                        "recommendation": recommendation
                                    }
                                }
                            )
                        except Exception as ws_err:
                            logger.error(f"Failed to broadcast WebSocket alert: {ws_err}")

            results.append({
                "zone": zname,
                "risk_score": round(risk_score, 4),
                "recommendation": recommendation,
                "severity": severity,
                "alert_id": str(alert.id) if alert else None
            })

        return results
