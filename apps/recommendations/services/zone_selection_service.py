import logging
from django.conf import settings
from django.db.models import Sum
from apps.warehouse.models import Zone, Bin

logger = logging.getLogger(__name__)

class ZoneSelectionService:
    """Selects and ranks Zones within a ZoneGroup based on capacity, utilization, priority, and active status.
    """

    @staticmethod
    def calculate_zone_capacity_metrics(zone: Zone):
        """Calculates total capacity, used capacity, available capacity, and utilization percentage.
        Queries Bins within the zone.
        """
        bins = Bin.objects.filter(shelf__rack__zone=zone)
        metrics = bins.aggregate(
            total_cap=Sum('max_capacity'),
            used_cap=Sum('current_capacity')
        )
        
        total_capacity = float(metrics['total_cap'] or 0.0)
        used_capacity = float(metrics['used_cap'] or 0.0)
        
        # If no bins or total capacity is 0, default to 100.0 total capacity, 0.0 used
        if total_capacity <= 0.0:
            total_capacity = 100.0
            used_capacity = 0.0
            
        available_capacity = total_capacity - used_capacity
        available_capacity_percentage = (available_capacity / total_capacity) * 100.0
        current_utilization_percentage = (used_capacity / total_capacity) * 100.0
        
        return {
            'total_capacity': total_capacity,
            'used_capacity': used_capacity,
            'available_capacity': available_capacity,
            'available_capacity_percentage': available_capacity_percentage,
            'current_utilization_percentage': current_utilization_percentage
        }

    @staticmethod
    def get_zone_priority(zone: Zone) -> float:
        """Returns zone priority score between 0.0 and 1.0 based on zone type or group description.
        """
        # Map zone types/codes to priority values
        priority_map = {
            'FAST_MOVING_STORAGE': 1.0,
            'FAST': 1.0,
            'SECURE_STORAGE': 0.9,
            'SECURE': 0.9,
            'HAZARDOUS_STORAGE': 0.8,
            'HAZARDOUS': 0.8,
            'COLD_STORAGE': 0.7,
            'COLD': 0.7,
            'FRAGILE_STORAGE': 0.6,
            'FRAGILE': 0.6,
            'BULK_STORAGE': 0.5,
            'BULK': 0.5,
            'GENERAL_STORAGE': 0.4,
            'GENERAL': 0.4,
            'SLOW_MOVING_STORAGE': 0.3,
            'SLOW': 0.3
        }
        
        # Check zone_type or zone_name
        ztype = (zone.zone_type or '').upper()
        if ztype in priority_map:
            return priority_map[ztype]
            
        # Check parent zone_group type if available
        if zone.zone_group and zone.zone_group.zone_group_type:
            zgtype = zone.zone_group.zone_group_type.upper()
            if zgtype in priority_map:
                return priority_map[zgtype]
                
        return 0.5  # default priority

    @staticmethod
    def is_zone_active(zone: Zone) -> bool:
        """Determines if a zone is active. Since there is no database column,
        zones are active by default.
        """
        return True

    def calculate_recommendation_score(self, capacity_pct: float, utilization_pct: float, priority: float, active: bool) -> float:
        """Calculates final score between 0.0 and 1.0.
        Weighting:
          - Capacity Score = 40%
          - Utilization Score = 30%
          - Priority Score = 20%
          - Zone Status Score = 10%
        """
        capacity_score = capacity_pct / 100.0
        # Lower utilization is better, so 100 - utilization_pct
        utilization_score = (100.0 - utilization_pct) / 100.0
        priority_score = priority
        status_score = 1.0 if active else 0.0
        
        score = (capacity_score * 0.4) + (utilization_score * 0.3) + (priority_score * 0.2) + (status_score * 0.1)
        return min(max(score, 0.0), 1.0)

    def select_best_zone(self, zone_group) -> tuple:
        """Selects the best Zone in the ZoneGroup using the capacity metrics and recommendation score.
        Rejects zones below WAREHOUSE_MIN_FREE_CAPACITY.
        """
        zones = Zone.objects.filter(zone_group=zone_group)
        if not zones.exists():
            # If no zones directly assigned, fallback to all zones in the same warehouse
            zones = Zone.objects.filter(warehouse=zone_group.warehouse)
            
        min_free = getattr(settings, 'WAREHOUSE_MIN_FREE_CAPACITY', 10)
        best_zone = None
        best_score = -1.0
        best_metrics = None
        
        absolute_best_zone = None
        absolute_best_score = -1.0
        absolute_best_metrics = None

        for zone in zones:
            if not self.is_zone_active(zone):
                continue
                
            metrics = self.calculate_zone_capacity_metrics(zone)
            free_pct = metrics['available_capacity_percentage']
            priority = self.get_zone_priority(zone)
            active_status = self.is_zone_active(zone)
            
            score = self.calculate_recommendation_score(
                capacity_pct=free_pct,
                utilization_pct=metrics['current_utilization_percentage'],
                priority=priority,
                active=active_status
            )
            
            if score > absolute_best_score:
                absolute_best_score = score
                absolute_best_zone = zone
                absolute_best_metrics = metrics
            
            # Reject zones below WAREHOUSE_MIN_FREE_CAPACITY
            if free_pct < min_free:
                logger.warning(
                    "ZoneSelectionService: Zone %s rejected. Free capacity %.2f%% is below minimum %s%%",
                    zone.zone_name, free_pct, min_free
                )
                continue
            
            logger.info(
                "ZoneSelectionService: Zone %s scored %.4f (free_pct=%.2f%%, utilization_pct=%.2f%%, priority=%.2f)",
                zone.zone_name, score, free_pct, metrics['current_utilization_percentage'], priority
            )
            
            if score > best_score:
                best_score = score
                best_zone = zone
                best_metrics = metrics
                
        if not best_zone:
            if absolute_best_zone:
                logger.warning(
                    "ZoneSelectionService: No zone met the minimum free capacity of %s%% in group %s. Falling back to %s with score %.4f.",
                    min_free, zone_group.code, absolute_best_zone.zone_name, absolute_best_score
                )
                return absolute_best_zone, absolute_best_score, absolute_best_metrics

            logger.error("ZoneSelectionService: No active zone with sufficient free capacity in group %s", zone_group.code)
            raise ValueError(f"No suitable zone found with at least {min_free}% free capacity")
            
        return best_zone, best_score, best_metrics
