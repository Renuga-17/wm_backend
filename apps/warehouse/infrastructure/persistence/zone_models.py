import uuid
from django.db import models
from .warehouse_models import Warehouse

class Zone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='zone_id')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, db_column='warehouse_id', related_name='zones')
    zone_name = models.CharField(max_length=100)
    zone_type = models.CharField(max_length=50)
    x = models.DecimalField(max_digits=10, decimal_places=4)
    y = models.DecimalField(max_digits=10, decimal_places=4)
    z = models.DecimalField(max_digits=10, decimal_places=4)
    width = models.DecimalField(max_digits=10, decimal_places=4)
    height = models.DecimalField(max_digits=10, decimal_places=4)
    depth = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        db_table = 'zones'

    def __str__(self):
        return f"{self.zone_name} ({self.zone_type})"

class WarehouseHeatmap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='heatmap_id')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, db_column='zone_id', related_name='heatmaps')
    activity_score = models.DecimalField(max_digits=5, decimal_places=4)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'warehouse_heatmaps'

    def __str__(self):
        return f"Heatmap {self.id} - Zone {self.zone.zone_name}"


class ZoneBoundary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='boundary_id')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, db_column='zone_id', related_name='boundaries')
    polygon_points = models.JSONField(default=list)  # list of vertices e.g., [{"x": 10.5, "y": 20.0}, ...]

    class Meta:
        db_table = 'zone_boundaries'

    def __str__(self):
        return f"Boundary for Zone {self.zone.zone_name}"


