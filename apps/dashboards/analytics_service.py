import logging
from datetime import datetime, timedelta
from django.utils import timezone
from apps.zones.models import Zone
from integrations.clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)

class WarehouseAnalyticsService:
    @staticmethod
    def _get_ch_client():
        try:
            return ClickHouseClient()
        except Exception as e:
            logger.error(f"ClickHouse client initialization failed: {e}")
            return None

    @staticmethod
    def _parse_time_range(start_str=None, end_str=None):
        """
        Parses start and end time strings, falling back to last 30 days if not provided.
        """
        now = datetime.utcnow()
        if not end_str:
            end_time = now
        else:
            try:
                end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            except ValueError:
                end_time = now

        if not start_str:
            start_time = end_time - timedelta(days=30)
        else:
            try:
                start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            except ValueError:
                start_time = end_time - timedelta(days=30)

        return start_time, end_time

    @classmethod
    def get_spatial_heatmap(cls, warehouse_id, start_str=None, end_str=None):
        """
        Aggregates activity counts and congestion scores by zone and aisle from warehouse_heatmaps.
        """
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return []

        # Get relevant zone names for this warehouse
        zones = Zone.objects.filter(warehouse_id=warehouse_id).values_list('zone_name', flat=True)
        if not zones:
            return []

        # Clickhouse query
        query = """
            SELECT 
                zone_code, 
                aisle_code, 
                sum(activity_count) as total_activity, 
                round(avg(avg_pick_time), 2) as avg_pick_time_sec, 
                round(avg(congestion_score), 4) as avg_congestion
            FROM warehouse_heatmaps
            WHERE heatmap_time >= %(start_time)s 
              AND heatmap_time <= %(end_time)s 
              AND zone_code IN %(zones)s
            GROUP BY zone_code, aisle_code
            ORDER BY total_activity DESC
        """
        params = {
            'start_time': start_time,
            'end_time': end_time,
            'zones': list(zones)
        }

        res = ch.execute_query(query, params=params)
        if not res:
            return []

        # Format output
        rows = []
        for row in res.result_rows:
            rows.append({
                'zone_code': row[0],
                'aisle_code': row[1],
                'total_activity': int(row[2]),
                'avg_pick_time_sec': float(row[3]),
                'avg_congestion': float(row[4])
            })
        return rows

    @classmethod
    def get_route_efficiency(cls, warehouse_id, start_str=None, end_str=None):
        """
        Calculates average travel times, total distance traversed, and route optimization rate.
        """
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return {}

        zones = Zone.objects.filter(warehouse_id=warehouse_id).values_list('zone_name', flat=True)
        if not zones:
            return {}

        query = """
            SELECT 
                vehicle_type, 
                count() as route_count, 
                round(avg(distance_meters), 2) as avg_distance, 
                round(avg(travel_time_seconds), 2) as avg_time_sec, 
                round(avg(congestion_level), 4) as avg_congestion,
                round(sum(optimized) * 100.0 / count(), 2) as optimization_percentage
            FROM route_analytics
            WHERE route_time >= %(start_time)s 
              AND route_time <= %(end_time)s 
              AND (source_zone IN %(zones)s OR destination_zone IN %(zones)s)
            GROUP BY vehicle_type
            ORDER BY route_count DESC
        """
        params = {
            'start_time': start_time,
            'end_time': end_time,
            'zones': list(zones)
        }

        res = ch.execute_query(query, params=params)
        if not res:
            return {}

        by_vehicle = {}
        total_routes = 0
        total_distance = 0.0
        total_time = 0.0
        optimized_routes = 0

        for row in res.result_rows:
            vtype = row[0]
            count = int(row[1])
            avg_dist = float(row[2])
            avg_time = float(row[3])
            avg_cong = float(row[4])
            opt_pct = float(row[5])

            by_vehicle[vtype] = {
                'route_count': count,
                'avg_distance_meters': avg_dist,
                'avg_travel_time_seconds': avg_time,
                'avg_congestion': avg_cong,
                'optimization_rate': opt_pct
            }
            total_routes += count
            total_distance += avg_dist * count
            total_time += avg_time * count
            optimized_routes += int(count * (opt_pct / 100.0))

        summary = {
            'total_routes': total_routes,
            'avg_distance_meters': round(total_distance / total_routes, 2) if total_routes > 0 else 0.0,
            'avg_travel_time_seconds': round(total_time / total_routes, 2) if total_routes > 0 else 0.0,
            'overall_optimization_rate': round(optimized_routes * 100.0 / total_routes, 2) if total_routes > 0 else 0.0,
            'vehicle_breakdown': by_vehicle
        }
        return summary

    @classmethod
    def get_sensor_telemetry_summary(cls, warehouse_id, start_str=None, end_str=None):
        """
        Exposes zone-by-zone environmental metrics (temperature, humidity, vibration).
        """
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return []

        zones = Zone.objects.filter(warehouse_id=warehouse_id).values_list('zone_name', flat=True)
        if not zones:
            return []

        query = """
            SELECT 
                zone_code, 
                round(avg(temperature), 2) as avg_temperature,
                round(min(temperature), 2) as min_temperature,
                round(max(temperature), 2) as max_temperature,
                round(avg(humidity), 2) as avg_humidity,
                round(avg(vibration), 4) as avg_vibration,
                count() as reading_count,
                sum(status = 'WARNING') as warnings_count
            FROM sensor_events
            WHERE event_time >= %(start_time)s 
              AND event_time <= %(end_time)s 
              AND zone_code IN %(zones)s
            GROUP BY zone_code
            ORDER BY zone_code ASC
        """
        params = {
            'start_time': start_time,
            'end_time': end_time,
            'zones': list(zones)
        }

        res = ch.execute_query(query, params=params)
        if not res:
            return []

        rows = []
        for row in res.result_rows:
            rows.append({
                'zone_code': row[0],
                'avg_temperature': float(row[1]),
                'min_temperature': float(row[2]),
                'max_temperature': float(row[3]),
                'avg_humidity': float(row[4]),
                'avg_vibration': float(row[5]),
                'reading_count': int(row[6]),
                'warnings_count': int(row[7])
            })
        return rows

    @classmethod
    def get_inventory_throughput(cls, warehouse_id, start_str=None, end_str=None):
        """
        Calculates pick vs. putaway activities and volume history over time.
        """
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return {}

        # 1. Total volumes by movement type
        volume_query = """
            SELECT 
                movement_type, 
                sum(quantity) as total_quantity, 
                count() as transaction_count
            FROM inventory_events
            WHERE warehouse_id = %(warehouse_id)s 
              AND event_time >= %(start_time)s 
              AND event_time <= %(end_time)s
            GROUP BY movement_type
        """
        params = {
            'warehouse_id': str(warehouse_id),
            'start_time': start_time,
            'end_time': end_time
        }

        vol_res = ch.execute_query(volume_query, params=params)
        totals = {}
        if vol_res:
            for row in vol_res.result_rows:
                totals[row[0].upper()] = {
                    'total_quantity': int(row[1]),
                    'transaction_count': int(row[2])
                }

        # Ensure both keys exist
        for k in ['PICK', 'PUTAWAY']:
            if k not in totals:
                totals[k] = {'total_quantity': 0, 'transaction_count': 0}

        # 2. Timeline history
        timeline_query = """
            SELECT 
                toDate(event_time) as event_date, 
                movement_type, 
                sum(quantity) as day_qty,
                count() as day_count
            FROM inventory_events
            WHERE warehouse_id = %(warehouse_id)s 
              AND event_time >= %(start_time)s 
              AND event_time <= %(end_time)s
            GROUP BY event_date, movement_type
            ORDER BY event_date ASC
        """
        time_res = ch.execute_query(timeline_query, params=params)
        timeline = {}
        if time_res:
            for row in time_res.result_rows:
                date_str = str(row[0])
                mtype = row[1].upper()
                qty = int(row[2])
                cnt = int(row[3])

                if date_str not in timeline:
                    timeline[date_str] = {'picks_qty': 0, 'picks_count': 0, 'putaways_qty': 0, 'putaways_count': 0}

                if mtype == 'PICK':
                    timeline[date_str]['picks_qty'] = qty
                    timeline[date_str]['picks_count'] = cnt
                elif mtype == 'PUTAWAY':
                    timeline[date_str]['putaways_qty'] = qty
                    timeline[date_str]['putaways_count'] = cnt

        # Format timeline list
        timeline_list = []
        for d, vals in sorted(timeline.items()):
            timeline_list.append({
                'date': d,
                **vals
            })

        # 3. Top products by volume
        top_prod_query = """
            SELECT 
                sku,
                product_name,
                sum(quantity) as vol,
                count() as txs
            FROM inventory_events
            WHERE warehouse_id = %(warehouse_id)s 
              AND event_time >= %(start_time)s 
              AND event_time <= %(end_time)s
            GROUP BY sku, product_name
            ORDER BY vol DESC
            LIMIT 5
        """
        top_res = ch.execute_query(top_prod_query, params=params)
        top_products = []
        if top_res:
            for row in top_res.result_rows:
                top_products.append({
                    'sku': row[0],
                    'product_name': row[1],
                    'volume': int(row[2]),
                    'transactions': int(row[3])
                })

        return {
            'summary': totals,
            'top_products': top_products,
            'timeline': timeline_list
        }
