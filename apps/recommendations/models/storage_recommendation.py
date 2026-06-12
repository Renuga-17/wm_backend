from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Import related models lazily to avoid circular imports
# Assuming existing Product model in apps.products.models
# and ZoneGroup, Zone models in apps.warehouse.models

class StorageRecommendation(models.Model):
    class RecommendationSource(models.TextChoices):
        RULE_ENGINE = 'RULE_ENGINE', 'Rule Engine'
        ML_MODEL = 'ML_MODEL', 'ML Model'
        # future sources can be added

    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='storage_recommendations')
    zone_group = models.ForeignKey('warehouse.ZoneGroup', on_delete=models.PROTECT, related_name='storage_recommendations')
    zone = models.ForeignKey('warehouse.Zone', on_delete=models.PROTECT, related_name='storage_recommendations')
    recommendation_reason = models.TextField()
    recommendation_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    recommendation_source = models.CharField(max_length=20, choices=RecommendationSource.choices)
    recommendation_version = models.CharField(max_length=20, default='v1')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['product', 'zone_group', 'zone'], name='storage_rec_query_idx'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"StorageRecommendation for {self.product_id} -> {self.zone_group_id}/{self.zone_id} (score={self.recommendation_score})"
