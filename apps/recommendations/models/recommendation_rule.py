from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

class RecommendationRule(models.Model):
    class MovementType(models.TextChoices):
        FAST = 'FAST', 'Fast Moving'
        SLOW = 'SLOW', 'Slow Moving'
        FRAGILE = 'FRAGILE', 'Fragile'
        HAZARDOUS = 'HAZARDOUS', 'Hazardous'
        # extend as needed

    class StorageType(models.TextChoices):
        GENERAL = 'GENERAL', 'General Storage'
        SECURE = 'SECURE', 'Secure Storage'
        COLD = 'COLD', 'Cold Storage'
        BULK = 'BULK', 'Bulk Storage'
        # extend as needed

    class ZoneGroupType(models.TextChoices):
        GENERAL_STORAGE = 'GENERAL_STORAGE', 'General Storage'
        SECURE_STORAGE = 'SECURE_STORAGE', 'Secure Storage'
        COLD_STORAGE = 'COLD_STORAGE', 'Cold Storage'
        BULK_STORAGE = 'BULK_STORAGE', 'Bulk Storage'
        FRAGILE_STORAGE = 'FRAGILE_STORAGE', 'Fragile Storage'
        HAZARDOUS_STORAGE = 'HAZARDOUS_STORAGE', 'Hazardous Storage'
        FAST_MOVING_STORAGE = 'FAST_MOVING_STORAGE', 'Fast Moving Storage'
        SLOW_MOVING_STORAGE = 'SLOW_MOVING_STORAGE', 'Slow Moving Storage'

    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    storage_type = models.CharField(max_length=20, choices=StorageType.choices)
    zone_group_type = models.CharField(max_length=30, choices=ZoneGroupType.choices)
    priority = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('movement_type', 'storage_type', 'zone_group_type')
        ordering = ['-priority']

    def __str__(self):
        return f"Rule {self.id}: {self.movement_type}/{self.storage_type} → {self.zone_group_type}"
