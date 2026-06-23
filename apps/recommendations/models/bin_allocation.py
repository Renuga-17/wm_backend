from django.db import models
from django.utils import timezone

class BinAllocation(models.Model):
    class AllocationSource(models.TextChoices):
        RULE_ENGINE = 'RULE_ENGINE', 'Rule Engine'

    class StorageStatus(models.TextChoices):
        ALLOCATED = 'ALLOCATED', 'Allocated'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        STORED = 'STORED', 'Stored'

    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='bin_allocations')
    zone_group = models.ForeignKey('warehouse.ZoneGroup', on_delete=models.PROTECT, related_name='bin_allocations')
    zone = models.ForeignKey('warehouse.Zone', on_delete=models.PROTECT, related_name='bin_allocations')
    rack = models.ForeignKey('warehouse.Rack', on_delete=models.PROTECT, related_name='bin_allocations')
    shelf = models.ForeignKey('warehouse.Shelf', on_delete=models.PROTECT, related_name='bin_allocations')
    bin = models.ForeignKey('warehouse.Bin', on_delete=models.PROTECT, related_name='bin_allocations')
    inbound_line = models.ForeignKey('inbound.InboundShipmentLine', on_delete=models.SET_NULL, null=True, blank=True, related_name='bin_allocations', db_column='inbound_line_id')
    inbound_shipment = models.ForeignKey('inbound.InboundShipment', on_delete=models.SET_NULL, null=True, blank=True, related_name='bin_allocations', db_column='inbound_shipment_id')
    
    allocation_score = models.FloatField()
    allocation_reason = models.TextField()
    allocation_source = models.CharField(max_length=20, choices=AllocationSource.choices, default=AllocationSource.RULE_ENGINE)
    allocation_version = models.CharField(max_length=10, default='v1')
    selected_orientation = models.CharField(max_length=50)
    
    navigation_instructions = models.TextField(blank=True, null=True)
    placement_instructions = models.TextField(blank=True, null=True)
    
    storage_status = models.CharField(max_length=20, choices=StorageStatus.choices, default=StorageStatus.ALLOCATED)
    stored_at = models.DateTimeField(blank=True, null=True)
    operator = models.CharField(max_length=150, blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bin_allocations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'zone', 'bin'], name='bin_alloc_query_idx'),
        ]

    def __str__(self):
        return f"BinAllocation for {self.product.id} -> Bin {self.bin.id} (Score: {self.allocation_score})"
