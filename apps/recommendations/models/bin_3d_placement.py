from django.db import models
from django.utils import timezone

class Bin3DPlacement(models.Model):
    class PlacementStrategy(models.TextChoices):
        BOTTOM_FLAT = 'BOTTOM_FLAT', 'Bottom Flat'
        STACKED = 'STACKED', 'Stacked'
        CORNER_ALIGN = 'CORNER_ALIGN', 'Corner Aligned'

    class LabelDirection(models.TextChoices):
        FRONT = 'FRONT', 'Facing Front'
        TOP = 'TOP', 'Facing Top'
        SIDE = 'SIDE', 'Facing Side'

    bin_allocation = models.OneToOneField(
        'recommendations.BinAllocation',
        on_delete=models.CASCADE,
        related_name='placement_3d'
    )
    occupied_volume = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    remaining_volume = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    utilization_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    placement_strategy = models.CharField(
        max_length=20,
        choices=PlacementStrategy.choices,
        default=PlacementStrategy.BOTTOM_FLAT
    )
    label_direction = models.CharField(
        max_length=20,
        choices=LabelDirection.choices,
        default=LabelDirection.FRONT
    )
    
    position_x = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    position_y = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    position_z = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'bin_3d_placements'
        ordering = ['-created_at']

    def __str__(self):
        return f"3D Placement for Alloc {self.bin_allocation_id} -> Position ({self.position_x}, {self.position_y}, {self.position_z})"
