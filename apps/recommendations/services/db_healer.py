import logging
from django.db import transaction
from apps.warehouse.models import Warehouse, ZoneGroup, Zone
from apps.recommendations.models.recommendation_rule import RecommendationRule

logger = logging.getLogger(__name__)

def ensure_default_setup():
    """Self-healing helper to ensure ZoneGroups, Zone linkages, and RecommendationRules exist in the database.
    """
    try:
        warehouse = Warehouse.objects.first()
        if not warehouse:
            logger.warning("db_healer: No warehouse found in database. Cannot run self-healing setup.")
            return

        with transaction.atomic():
            # 1. Ensure GENERAL_STORAGE ZoneGroup exists
            general_zg, created_gen = ZoneGroup.objects.get_or_create(
                zone_group_type='GENERAL_STORAGE',
                defaults={
                    'warehouse': warehouse,
                    'code': 'ZG-GEN',
                    'name': 'General Storage Zone Group',
                    'description': 'Auto-created general storage zone group'
                }
            )
            if created_gen:
                logger.info("db_healer: Created GENERAL_STORAGE ZoneGroup.")

            # 2. Ensure COLD_STORAGE ZoneGroup exists
            cold_zg, created_cold = ZoneGroup.objects.get_or_create(
                zone_group_type='COLD_STORAGE',
                defaults={
                    'warehouse': warehouse,
                    'code': 'ZG-COLD',
                    'name': 'Cold Storage Zone Group',
                    'description': 'Auto-created cold storage zone group'
                }
            )
            if created_cold:
                logger.info("db_healer: Created COLD_STORAGE ZoneGroup.")

            # 3. Link unassigned Zones to their respective ZoneGroup based on name
            # Zone A*, B*, C* -> GENERAL_STORAGE
            # Zone D* -> COLD_STORAGE
            unassigned_zones = Zone.objects.filter(zone_group__isnull=True)
            for zone in unassigned_zones:
                name_upper = zone.zone_name.upper()
                if any(x in name_upper for x in ['ZONE A', 'ZONE B', 'ZONE C', 'A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'C4']):
                    zone.zone_group = general_zg
                    zone.save()
                    logger.info("db_healer: Linked zone %s to GENERAL_STORAGE.", zone.zone_name)
                elif any(x in name_upper for x in ['ZONE D', 'D1', 'D2', 'D3']):
                    zone.zone_group = cold_zg
                    zone.save()
                    logger.info("db_healer: Linked zone %s to COLD_STORAGE.", zone.zone_name)
                else:
                    # Default fallback to general storage
                    zone.zone_group = general_zg
                    zone.save()
                    logger.info("db_healer: Linked zone %s to GENERAL_STORAGE by default.", zone.zone_name)

            # 4. Ensure RecommendationRules exist
            rules_to_create = [
                # FAST / SLOW / FRAGILE / HAZARDOUS for GENERAL storage
                ('FAST', 'GENERAL', 'GENERAL_STORAGE', 10, 'Auto-created fast general storage rule'),
                ('SLOW', 'GENERAL', 'GENERAL_STORAGE', 5, 'Auto-created slow general storage rule'),
                ('FRAGILE', 'GENERAL', 'GENERAL_STORAGE', 10, 'Auto-created fragile general storage rule'),
                ('HAZARDOUS', 'GENERAL', 'GENERAL_STORAGE', 10, 'Auto-created hazardous general storage rule'),
                # COLD storage rules
                ('FAST', 'COLD', 'COLD_STORAGE', 20, 'Auto-created fast cold storage rule'),
                ('SLOW', 'COLD', 'COLD_STORAGE', 10, 'Auto-created slow cold storage rule'),
            ]

            for m_type, s_type, zg_type, priority, desc in rules_to_create:
                rule, created = RecommendationRule.objects.get_or_create(
                    movement_type=m_type,
                    storage_type=s_type,
                    zone_group_type=zg_type,
                    defaults={
                        'priority': priority,
                        'description': desc
                    }
                )
                if created:
                    logger.info("db_healer: Created RecommendationRule %s/%s -> %s.", m_type, s_type, zg_type)

    except Exception as e:
        logger.exception("db_healer: Error running self-healing setup: %s", str(e))
