import logging
from decimal import Decimal
from django.db import transaction
from django.db.models import Count, Q
from asgiref.sync import async_to_sync
from apps.warehouse.models import Bin, Rack, Zone, Warehouse

logger = logging.getLogger(__name__)


class DigitalTwinSyncService:
    @staticmethod
    def calculate_rack_occupancy(rack: Rack) -> dict:
        """Dynamically aggregate occupancy metrics for a Rack."""
        metrics = Bin.objects.filter(shelf__rack=rack).aggregate(
            total_bins=Count('id'),
            occupied_bins=Count('id', filter=Q(is_occupied=True))
        )
        total = metrics['total_bins'] or 0
        occupied = metrics['occupied_bins'] or 0
        percentage = (occupied / total * 100.0) if total > 0 else 0.0
        return {
            'rack_id': str(rack.id),
            'rack_code': rack.rack_code,
            'total_bins': total,
            'occupied_bins': occupied,
            'occupancy_percentage': round(percentage, 2)
        }

    @staticmethod
    def calculate_zone_occupancy(zone: Zone) -> dict:
        """Dynamically aggregate occupancy metrics for a Zone."""
        metrics = Bin.objects.filter(shelf__rack__zone=zone).aggregate(
            total_bins=Count('id'),
            occupied_bins=Count('id', filter=Q(is_occupied=True))
        )
        total = metrics['total_bins'] or 0
        occupied = metrics['occupied_bins'] or 0
        percentage = (occupied / total * 100.0) if total > 0 else 0.0
        return {
            'zone_id': str(zone.id),
            'zone_name': zone.zone_name,
            'total_bins': total,
            'occupied_bins': occupied,
            'occupancy_percentage': round(percentage, 2)
        }

    @staticmethod
    def calculate_warehouse_occupancy(warehouse: Warehouse) -> dict:
        """Dynamically aggregate occupancy metrics for a Warehouse."""
        metrics = Bin.objects.filter(shelf__rack__zone__warehouse=warehouse).aggregate(
            total_bins=Count('id'),
            occupied_bins=Count('id', filter=Q(is_occupied=True))
        )
        total = metrics['total_bins'] or 0
        occupied = metrics['occupied_bins'] or 0
        percentage = (occupied / total * 100.0) if total > 0 else 0.0
        return {
            'warehouse_id': str(warehouse.id),
            'warehouse_name': warehouse.name,
            'total_bins': total,
            'occupied_bins': occupied,
            'occupancy_percentage': round(percentage, 2)
        }

    @classmethod
    def sync_occupancy(cls, bin_id, is_occupied: bool, current_capacity: Decimal = None, capacity_delta: Decimal = None) -> dict:
        """
        Atomically updates the bin occupancy state, dynamically calculates 
        parent rack, zone, and warehouse metrics, and broadcasts updates via WebSockets.
        """
        logger.info("DigitalTwinSyncService: Syncing occupancy for bin %s (is_occupied=%s)", bin_id, is_occupied)
        
        with transaction.atomic():
            # Atomically lock the bin row
            bin_obj = Bin.objects.select_for_update().get(id=bin_id)
            
            bin_obj.is_occupied = is_occupied
            if current_capacity is not None:
                bin_obj.current_capacity = Decimal(str(current_capacity))
            elif capacity_delta is not None:
                bin_obj.current_capacity = bin_obj.current_capacity + Decimal(str(capacity_delta))
                
            # Keep current_capacity within bounds
            if bin_obj.current_capacity < 0:
                bin_obj.current_capacity = Decimal('0.00')
            if bin_obj.current_capacity > bin_obj.max_capacity:
                bin_obj.current_capacity = bin_obj.max_capacity
                
            bin_obj.save()
            
            # Fetch parents
            shelf = bin_obj.shelf
            rack = shelf.rack
            zone = rack.zone
            warehouse = zone.warehouse

            # Dynamic SQL Aggregations
            rack_metrics = cls.calculate_rack_occupancy(rack)
            zone_metrics = cls.calculate_zone_occupancy(zone)
            warehouse_metrics = cls.calculate_warehouse_occupancy(warehouse)

        # Construct payload with backward compatibility and nested properties
        payload = {
            'bin_code': bin_obj.bin_code,
            'is_occupied': bin_obj.is_occupied,
            'current_capacity': float(bin_obj.current_capacity),
            'rack': rack_metrics,
            'zone': zone_metrics,
            'warehouse': warehouse_metrics
        }

        # WebSocket Broadcast
        try:
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    'occupancy_updates',
                    {
                        'type': 'occupancy_message',
                        'message': payload
                    }
                )
                logger.info("DigitalTwinSyncService: Websocket broadcast succeeded.")
        except Exception as ws_err:
            logger.warning("DigitalTwinSyncService: Websocket broadcast failed: %s", ws_err)

        return payload
