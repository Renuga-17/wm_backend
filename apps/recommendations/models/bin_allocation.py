from django.db import models
from django.utils import timezone

class BinAllocation(models.Model):
    class AllocationSource(models.TextChoices):
        RULE_ENGINE = 'RULE_ENGINE', 'Rule Engine'

    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='bin_allocations')
    zone_group = models.ForeignKey('warehouse.ZoneGroup', on_delete=models.PROTECT, related_name='bin_allocations')
    zone = models.ForeignKey('warehouse.Zone', on_delete=models.PROTECT, related_name='bin_allocations')
    rack = models.ForeignKey('warehouse.Rack', on_delete=models.PROTECT, related_name='bin_allocations')
    shelf = models.ForeignKey('warehouse.Shelf', on_delete=models.PROTECT, related_name='bin_allocations')
    bin = models.ForeignKey('warehouse.Bin', on_delete=models.PROTECT, related_name='bin_allocations')
    
    allocation_score = models.FloatField()
    allocation_reason = models.TextField()
    allocation_source = models.CharField(max_length=20, choices=AllocationSource.choices, default=AllocationSource.RULE_ENGINE)
    allocation_version = models.CharField(max_length=10, default='v1')
    selected_orientation = models.CharField(max_length=50)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bin_allocations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'zone', 'bin'], name='bin_alloc_query_idx'),
        ]

    def __str__(self):
        return f"BinAllocation for {self.product_id} -> Bin {self.bin_id} (Score: {self.allocation_score})"
