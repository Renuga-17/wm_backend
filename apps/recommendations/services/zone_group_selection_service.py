import logging
from django.conf import settings
from django.db.models import F
from ..models.recommendation_rule import RecommendationRule
from apps.warehouse.models import ZoneGroup, Zone

logger = logging.getLogger(__name__)

class ZoneGroupSelectionService:
    """Select a ZoneGroup based on movement/storage type, priority and capacity.

    The selection algorithm:
    1. Filter RecommendationRule by movement_type and storage_type.
    2. Order by -priority.
    3. For each rule, check the associated ZoneGroup meets the free capacity
       requirement (percentage based) using the configured
       ``WAREHOUSE_MIN_FREE_CAPACITY``.
    4. Return the first matching ZoneGroup.
    """

    @staticmethod
    def _free_capacity_percentage(zone_group: ZoneGroup) -> float:
        """Calculate free capacity percentage for a ZoneGroup.
        """
        from apps.warehouse.models import Bin
        from django.db.models import Sum
        
        bins = Bin.objects.filter(shelf__rack__zone__zone_group=zone_group)
        metrics = bins.aggregate(
            total_cap=Sum('max_capacity'),
            used_cap=Sum('current_capacity')
        )
        
        total_capacity = float(metrics['total_cap'] or 0.0)
        used_capacity = float(metrics['used_cap'] or 0.0)
        
        if total_capacity <= 0.0:
            return 100.0
            
        free_percent = ((total_capacity - used_capacity) / total_capacity) * 100.0
        return free_percent

    def select(self, movement_type: str, storage_type: str) -> ZoneGroup:
        from .db_healer import ensure_default_setup
        ensure_default_setup()

        # Step 1: matching rules
        rules = RecommendationRule.objects.filter(
            movement_type=movement_type,
            storage_type=storage_type,
        ).order_by('-priority')
        logger.info(
            "ZoneGroupSelectionService: found %d rules for %s/%s",
            rules.count(), movement_type, storage_type,
        )
        min_free = getattr(settings, "WAREHOUSE_MIN_FREE_CAPACITY", 10)
        first_valid_zg = None
        for rule in rules:
            try:
                zg = ZoneGroup.objects.get(zone_group_type=rule.zone_group_type)
            except ZoneGroup.DoesNotExist:
                logger.warning("ZoneGroup %s does not exist", rule.zone_group_type)
                continue
            
            if first_valid_zg is None:
                first_valid_zg = zg

            free_pct = self._free_capacity_percentage(zg)
            logger.debug(
                "Evaluated ZoneGroup %s: free_pct=%.2f (min required=%s)",
                zg.zone_group_type, free_pct, min_free,
            )
            if free_pct >= min_free:
                logger.info("Selected ZoneGroup %s based on rule %s", zg.zone_group_type, rule.id)
                return zg
        
        if first_valid_zg:
            logger.warning(
                "ZoneGroupSelectionService: No ZoneGroup met the minimum free capacity of %s%%. Falling back to %s.",
                min_free, first_valid_zg.zone_group_type
            )
            return first_valid_zg

        logger.error("No suitable ZoneGroup found for %s/%s", movement_type, storage_type)
        raise ValueError("No suitable ZoneGroup found")
