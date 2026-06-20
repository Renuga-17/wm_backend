import json
import logging
import uuid
from datetime import datetime, timedelta

from django.db.models import Avg, Count, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.warehouse.infrastructure.persistence.models import (
    Bin, Rack, Shelf, Zone,
)
from integrations.clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)


class WarehouseAnalyticsService:
    """
    Unified analytics service: event ingestion (writes) and dashboard queries (reads).
    All ClickHouse interactions go through the existing ClickHouseClient.
    """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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

    # ==================================================================
    # EVENT TRACKING (PIPELINE) — writes to ClickHouse
    # ==================================================================

    @classmethod
    def track_warehouse_event(cls, event_type, warehouse_id, entity_type,
                              entity_id, metadata=None):
        """
        Record a generic operational event into the warehouse_events table.

        Covers: Inbound, Inventory, Outbound, Recommendation, Digital Twin,
        and Route event categories.
        """
        ch = cls._get_ch_client()
        if not ch:
            return False

        row = {
            'event_id': str(uuid.uuid4()),
            'event_type': str(event_type),
            'warehouse_id': str(warehouse_id),
            'entity_type': str(entity_type),
            'entity_id': str(entity_id),
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'metadata_json': json.dumps(metadata or {}),
        }
        return ch.insert_row('warehouse_events', row)

    @classmethod
    def track_recommendation_metric(cls, recommendation_id, warehouse_id,
                                    score, accepted, travel_distance=0.0):
        """Record recommendation scoring / acceptance into recommendation_metrics."""
        ch = cls._get_ch_client()
        if not ch:
            return False

        row = {
            'recommendation_id': str(recommendation_id),
            'warehouse_id': str(warehouse_id),
            'score': float(score),
            'accepted': 1 if accepted else 0,
            'travel_distance': float(travel_distance),
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        }
        return ch.insert_row('recommendation_metrics', row)

    @classmethod
    def track_occupancy_metric(cls, warehouse_id, zone_id, rack_id,
                               occupancy_percentage):
        """Record an occupancy snapshot into occupancy_metrics."""
        ch = cls._get_ch_client()
        if not ch:
            return False

        row = {
            'warehouse_id': str(warehouse_id),
            'zone_id': str(zone_id),
            'rack_id': str(rack_id or ''),
            'occupancy_percentage': float(occupancy_percentage),
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        }
        return ch.insert_row('occupancy_metrics', row)

    @classmethod
    def track_route_metric(cls, route_id, warehouse_id, distance,
                           nodes_visited, optimization_score=0.0):
        """Record a route metric snapshot into route_metrics."""
        ch = cls._get_ch_client()
        if not ch:
            return False

        row = {
            'route_id': str(route_id),
            'warehouse_id': str(warehouse_id),
            'distance': float(distance),
            'nodes_visited': int(nodes_visited),
            'optimization_score': float(optimization_score),
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        }
        return ch.insert_row('route_metrics', row)

    # ==================================================================
    # EXISTING QUERY METHODS (preserved from original)
    # ==================================================================

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

    # ==================================================================
    # NEW DASHBOARD QUERY METHODS
    # ==================================================================

    @classmethod
    def get_warehouse_kpis(cls, warehouse_id, start_str=None, end_str=None):
        """
        Aggregated KPI dashboard: total events by type, avg occupancy, event velocity.
        """
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return {}

        # Events by type
        event_query = """
            SELECT
                event_type,
                count() as event_count
            FROM warehouse_events
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
            GROUP BY event_type
            ORDER BY event_count DESC
        """
        params = {
            'warehouse_id': str(warehouse_id),
            'start_time': start_time,
            'end_time': end_time,
        }

        res = ch.execute_query(event_query, params=params)
        events_by_type = {}
        total_events = 0
        if res:
            for row in res.result_rows:
                events_by_type[row[0]] = int(row[1])
                total_events += int(row[1])

        # Average occupancy
        occ_query = """
            SELECT
                round(avg(occupancy_percentage), 2) as avg_occupancy
            FROM occupancy_metrics
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
        """
        occ_res = ch.execute_query(occ_query, params=params)
        avg_occupancy = 0.0
        if occ_res and occ_res.result_rows:
            val = occ_res.result_rows[0][0]
            avg_occupancy = float(val) if val is not None else 0.0

        # Daily event velocity
        velocity_query = """
            SELECT
                toDate(timestamp) as event_date,
                count() as daily_count
            FROM warehouse_events
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
            GROUP BY event_date
            ORDER BY event_date ASC
        """
        vel_res = ch.execute_query(velocity_query, params=params)
        daily_velocity = []
        if vel_res:
            for row in vel_res.result_rows:
                daily_velocity.append({
                    'date': str(row[0]),
                    'event_count': int(row[1]),
                })

        return {
            'total_events': total_events,
            'events_by_type': events_by_type,
            'avg_occupancy_pct': avg_occupancy,
            'daily_velocity': daily_velocity,
        }

    @classmethod
    def get_occupancy_trends(cls, warehouse_id, start_str=None, end_str=None):
        """Time-series occupancy by zone."""
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return []

        query = """
            SELECT
                zone_id,
                toDate(timestamp) as occ_date,
                round(avg(occupancy_percentage), 2) as avg_occ
            FROM occupancy_metrics
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
            GROUP BY zone_id, occ_date
            ORDER BY occ_date ASC, zone_id ASC
        """
        params = {
            'warehouse_id': str(warehouse_id),
            'start_time': start_time,
            'end_time': end_time,
        }

        res = ch.execute_query(query, params=params)
        if not res:
            return []

        rows = []
        for row in res.result_rows:
            rows.append({
                'zone_id': row[0],
                'date': str(row[1]),
                'avg_occupancy_pct': float(row[2]),
            })
        return rows

    @classmethod
    def get_inventory_movements(cls, warehouse_id, start_str=None, end_str=None):
        """Inventory movement events (Relocation, Transfer, Adjustment, Damage, Audit)."""
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return []

        inventory_types = [
            'RELOCATION', 'TRANSFER', 'ADJUSTMENT', 'DAMAGE', 'AUDIT',
        ]

        query = """
            SELECT
                event_type,
                entity_type,
                count() as event_count,
                toDate(timestamp) as event_date
            FROM warehouse_events
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
              AND event_type IN %(event_types)s
            GROUP BY event_type, entity_type, event_date
            ORDER BY event_date ASC
        """
        params = {
            'warehouse_id': str(warehouse_id),
            'start_time': start_time,
            'end_time': end_time,
            'event_types': inventory_types,
        }

        res = ch.execute_query(query, params=params)
        if not res:
            return []

        rows = []
        for row in res.result_rows:
            rows.append({
                'event_type': row[0],
                'entity_type': row[1],
                'event_count': int(row[2]),
                'date': str(row[3]),
            })
        return rows

    @classmethod
    def get_inbound_metrics(cls, warehouse_id, start_str=None, end_str=None):
        """Inbound events (SHIPMENT_CREATED, OCR_PROCESSED, PRODUCT_CREATED, ALLOCATION_CREATED)."""
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return {}

        inbound_types = [
            'SHIPMENT_CREATED', 'OCR_PROCESSED', 'PRODUCT_CREATED', 'ALLOCATION_CREATED',
        ]

        summary_query = """
            SELECT
                event_type,
                count() as event_count
            FROM warehouse_events
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
              AND event_type IN %(event_types)s
            GROUP BY event_type
        """
        params = {
            'warehouse_id': str(warehouse_id),
            'start_time': start_time,
            'end_time': end_time,
            'event_types': inbound_types,
        }

        res = ch.execute_query(summary_query, params=params)
        summary = {}
        total = 0
        if res:
            for row in res.result_rows:
                summary[row[0]] = int(row[1])
                total += int(row[1])

        # Timeline
        timeline_query = """
            SELECT
                toDate(timestamp) as event_date,
                count() as daily_count
            FROM warehouse_events
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
              AND event_type IN %(event_types)s
            GROUP BY event_date
            ORDER BY event_date ASC
        """
        tl_res = ch.execute_query(timeline_query, params=params)
        timeline = []
        if tl_res:
            for row in tl_res.result_rows:
                timeline.append({
                    'date': str(row[0]),
                    'count': int(row[1]),
                })

        return {
            'total_inbound_events': total,
            'by_type': summary,
            'timeline': timeline,
        }

    @classmethod
    def get_outbound_metrics(cls, warehouse_id, start_str=None, end_str=None):
        """Outbound events (PICK_LIST_GENERATED, PICKER_ASSIGNED, ROUTE_OPTIMIZED, PACKED, DISPATCHED, CLOSED)."""
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return {}

        outbound_types = [
            'PICK_LIST_GENERATED', 'PICKER_ASSIGNED', 'ROUTE_OPTIMIZED',
            'PACKED', 'DISPATCHED', 'CLOSED',
        ]

        summary_query = """
            SELECT
                event_type,
                count() as event_count
            FROM warehouse_events
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
              AND event_type IN %(event_types)s
            GROUP BY event_type
        """
        params = {
            'warehouse_id': str(warehouse_id),
            'start_time': start_time,
            'end_time': end_time,
            'event_types': outbound_types,
        }

        res = ch.execute_query(summary_query, params=params)
        summary = {}
        total = 0
        if res:
            for row in res.result_rows:
                summary[row[0]] = int(row[1])
                total += int(row[1])

        # Timeline
        timeline_query = """
            SELECT
                toDate(timestamp) as event_date,
                count() as daily_count
            FROM warehouse_events
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
              AND event_type IN %(event_types)s
            GROUP BY event_date
            ORDER BY event_date ASC
        """
        tl_res = ch.execute_query(timeline_query, params=params)
        timeline = []
        if tl_res:
            for row in tl_res.result_rows:
                timeline.append({
                    'date': str(row[0]),
                    'count': int(row[1]),
                })

        return {
            'total_outbound_events': total,
            'by_type': summary,
            'timeline': timeline,
        }

    @classmethod
    def get_recommendation_metrics(cls, warehouse_id, start_str=None, end_str=None):
        """Recommendation acceptance rate, avg score, avg travel distance."""
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return {}

        query = """
            SELECT
                count() as total,
                sum(accepted) as accepted_count,
                round(avg(score), 4) as avg_score,
                round(avg(travel_distance), 2) as avg_travel_distance,
                round(sum(accepted) * 100.0 / count(), 2) as acceptance_rate
            FROM recommendation_metrics
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
        """
        params = {
            'warehouse_id': str(warehouse_id),
            'start_time': start_time,
            'end_time': end_time,
        }

        res = ch.execute_query(query, params=params)
        if not res or not res.result_rows:
            return {
                'total_recommendations': 0,
                'accepted_count': 0,
                'acceptance_rate': 0.0,
                'avg_score': 0.0,
                'avg_travel_distance': 0.0,
            }

        row = res.result_rows[0]
        total = int(row[0]) if row[0] else 0

        # Timeline
        tl_query = """
            SELECT
                toDate(timestamp) as metric_date,
                count() as daily_total,
                sum(accepted) as daily_accepted
            FROM recommendation_metrics
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
            GROUP BY metric_date
            ORDER BY metric_date ASC
        """
        tl_res = ch.execute_query(tl_query, params=params)
        timeline = []
        if tl_res:
            for tl_row in tl_res.result_rows:
                timeline.append({
                    'date': str(tl_row[0]),
                    'total': int(tl_row[1]),
                    'accepted': int(tl_row[2]),
                })

        return {
            'total_recommendations': total,
            'accepted_count': int(row[1]) if row[1] else 0,
            'acceptance_rate': float(row[4]) if row[4] and total > 0 else 0.0,
            'avg_score': float(row[2]) if row[2] else 0.0,
            'avg_travel_distance': float(row[3]) if row[3] else 0.0,
            'timeline': timeline,
        }

    @classmethod
    def get_route_metrics(cls, warehouse_id, start_str=None, end_str=None):
        """Route optimization metrics: distance, nodes, optimization score."""
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return {}

        query = """
            SELECT
                count() as total_routes,
                round(avg(distance), 2) as avg_distance,
                round(avg(nodes_visited), 2) as avg_nodes,
                round(avg(optimization_score), 4) as avg_optimization_score,
                round(min(distance), 2) as min_distance,
                round(max(distance), 2) as max_distance
            FROM route_metrics
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
        """
        params = {
            'warehouse_id': str(warehouse_id),
            'start_time': start_time,
            'end_time': end_time,
        }

        res = ch.execute_query(query, params=params)
        if not res or not res.result_rows:
            return {
                'total_routes': 0,
                'avg_distance': 0.0,
                'avg_nodes_visited': 0.0,
                'avg_optimization_score': 0.0,
            }

        row = res.result_rows[0]

        # Timeline
        tl_query = """
            SELECT
                toDate(timestamp) as metric_date,
                count() as daily_routes,
                round(avg(distance), 2) as daily_avg_dist
            FROM route_metrics
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
            GROUP BY metric_date
            ORDER BY metric_date ASC
        """
        tl_res = ch.execute_query(tl_query, params=params)
        timeline = []
        if tl_res:
            for tl_row in tl_res.result_rows:
                timeline.append({
                    'date': str(tl_row[0]),
                    'routes': int(tl_row[1]),
                    'avg_distance': float(tl_row[2]),
                })

        return {
            'total_routes': int(row[0]) if row[0] else 0,
            'avg_distance': float(row[1]) if row[1] else 0.0,
            'avg_nodes_visited': float(row[2]) if row[2] else 0.0,
            'avg_optimization_score': float(row[3]) if row[3] else 0.0,
            'min_distance': float(row[4]) if row[4] else 0.0,
            'max_distance': float(row[5]) if row[5] else 0.0,
            'timeline': timeline,
        }

    @classmethod
    def get_top_zones(cls, warehouse_id, start_str=None, end_str=None, limit=10):
        """Most active zones by event count."""
        start_time, end_time = cls._parse_time_range(start_str, end_str)
        ch = cls._get_ch_client()
        if not ch:
            return []

        query = """
            SELECT
                JSONExtractString(metadata_json, 'zone_id') as zone_id,
                JSONExtractString(metadata_json, 'zone_name') as zone_name,
                count() as event_count
            FROM warehouse_events
            WHERE warehouse_id = %(warehouse_id)s
              AND timestamp >= %(start_time)s
              AND timestamp <= %(end_time)s
              AND JSONExtractString(metadata_json, 'zone_id') != ''
            GROUP BY zone_id, zone_name
            ORDER BY event_count DESC
            LIMIT %(limit)s
        """
        params = {
            'warehouse_id': str(warehouse_id),
            'start_time': start_time,
            'end_time': end_time,
            'limit': int(limit),
        }

        res = ch.execute_query(query, params=params)
        if not res:
            return []

        rows = []
        for row in res.result_rows:
            rows.append({
                'zone_id': row[0],
                'zone_name': row[1] or row[0],
                'event_count': int(row[2]),
            })
        return rows

    # ==================================================================
    # HEATMAP METHODS (Django ORM — live warehouse hierarchy data)
    # ==================================================================

    @classmethod
    def get_zone_heatmap(cls, warehouse_id):
        """
        Zone-level utilization heatmap.
        Calculates occupancy from bins within each zone via Warehouse → Zone → Rack → Shelf → Bin.
        """
        zones = Zone.objects.filter(warehouse_id=warehouse_id)
        if not zones.exists():
            return []

        result = []
        for zone in zones:
            bins_qs = Bin.objects.filter(
                shelf__rack__zone=zone
            )
            total_capacity = 0.0
            used_capacity = 0.0
            total_bins = 0
            occupied_bins = 0

            for b in bins_qs:
                total_capacity += float(b.max_capacity)
                used_capacity += float(b.current_capacity)
                total_bins += 1
                if b.is_occupied:
                    occupied_bins += 1

            occupancy_pct = round(
                (used_capacity / total_capacity * 100) if total_capacity > 0 else 0.0, 2
            )
            result.append({
                'zone_id': str(zone.id),
                'zone_name': zone.zone_name,
                'zone_type': zone.zone_type,
                'total_bins': total_bins,
                'occupied_bins': occupied_bins,
                'total_capacity': total_capacity,
                'used_capacity': used_capacity,
                'occupancy_pct': occupancy_pct,
            })

        return sorted(result, key=lambda x: x['occupancy_pct'], reverse=True)

    @classmethod
    def get_rack_heatmap(cls, warehouse_id, zone_id=None):
        """
        Rack-level utilization heatmap.
        Optionally filtered by zone_id.
        """
        rack_qs = Rack.objects.filter(zone__warehouse_id=warehouse_id)
        if zone_id:
            rack_qs = rack_qs.filter(zone_id=zone_id)

        if not rack_qs.exists():
            return []

        result = []
        for rack in rack_qs:
            bins_qs = Bin.objects.filter(shelf__rack=rack)
            total_capacity = 0.0
            used_capacity = 0.0
            total_bins = 0
            occupied_bins = 0

            for b in bins_qs:
                total_capacity += float(b.max_capacity)
                used_capacity += float(b.current_capacity)
                total_bins += 1
                if b.is_occupied:
                    occupied_bins += 1

            occupancy_pct = round(
                (used_capacity / total_capacity * 100) if total_capacity > 0 else 0.0, 2
            )
            result.append({
                'rack_id': str(rack.id),
                'rack_code': rack.rack_code,
                'zone_id': str(rack.zone_id),
                'total_bins': total_bins,
                'occupied_bins': occupied_bins,
                'total_capacity': total_capacity,
                'used_capacity': used_capacity,
                'occupancy_pct': occupancy_pct,
            })

        return sorted(result, key=lambda x: x['occupancy_pct'], reverse=True)

    @classmethod
    def get_bin_utilization_heatmap(cls, warehouse_id, zone_id=None,
                                    rack_id=None):
        """
        Bin-level utilization heatmap.
        Optionally filtered by zone_id and/or rack_id.
        """
        bin_qs = Bin.objects.filter(
            shelf__rack__zone__warehouse_id=warehouse_id
        )
        if zone_id:
            bin_qs = bin_qs.filter(shelf__rack__zone_id=zone_id)
        if rack_id:
            bin_qs = bin_qs.filter(shelf__rack_id=rack_id)

        if not bin_qs.exists():
            return []

        result = []
        for b in bin_qs:
            max_cap = float(b.max_capacity)
            cur_cap = float(b.current_capacity)
            occupancy_pct = round(
                (cur_cap / max_cap * 100) if max_cap > 0 else 0.0, 2
            )
            result.append({
                'bin_id': str(b.id),
                'bin_code': b.bin_code,
                'rack_id': str(b.shelf.rack_id),
                'max_capacity': max_cap,
                'current_capacity': cur_cap,
                'is_occupied': b.is_occupied,
                'occupancy_pct': occupancy_pct,
            })

        return sorted(result, key=lambda x: x['occupancy_pct'], reverse=True)
