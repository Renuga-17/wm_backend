import uuid
from django.db import models
from .zone_models import ZoneGroup, Zone

class RecommendationRule(models.Model):
    class Meta:
        db_table = "recommendation_rules"
        ordering = ["priority"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column="rule_id")
    movement_type = models.CharField(max_length=30, db_column="movement_type")
    storage_type = models.CharField(max_length=30, db_column="storage_type")
    zone_group_type = models.CharField(
        max_length=30,
        db_column="zone_group_type",
        choices=[
            ("GENERAL_STORAGE", "GENERAL_STORAGE"),
            ("SECURE_STORAGE", "SECURE_STORAGE"),
            ("COLD_STORAGE", "COLD_STORAGE"),
            ("BULK_STORAGE", "BULK_STORAGE"),
            ("FRAGILE_STORAGE", "FRAGILE_STORAGE"),
            ("HAZARDOUS_STORAGE", "HAZARDOUS_STORAGE"),
            ("FAST_MOVING_STORAGE", "FAST_MOVING_STORAGE"),
            ("SLOW_MOVING_STORAGE", "SLOW_MOVING_STORAGE"),
        ],
    )
    priority = models.PositiveIntegerField(default=100, db_column="priority")
    description = models.TextField(blank=True, null=True, db_column="description")
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at")
    updated_at = models.DateTimeField(auto_now=True, db_column="updated_at")

    def __str__(self):
        return f"Rule {self.id} - {self.movement_type}/{self.storage_type} -> {self.zone_group_type}"
