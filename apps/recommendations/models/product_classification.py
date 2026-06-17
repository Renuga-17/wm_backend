from django.db import models
from django.utils import timezone
from .recommendation_rule import RecommendationRule

class ProductClassification(models.Model):
    product = models.OneToOneField('inventory.Product', on_delete=models.CASCADE, related_name='classification')
    movement_type = models.CharField(max_length=20, choices=RecommendationRule.MovementType.choices)
    storage_type = models.CharField(max_length=20, choices=RecommendationRule.StorageType.choices)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Classification for {self.product.sku}: {self.movement_type}/{self.storage_type}"
