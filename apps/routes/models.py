import uuid
from django.db import models
from apps.warehouses.models import Warehouse

class OptimizedRoute(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='route_id')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='optimized_routes', null=True)
    start_location = models.CharField(max_length=100)
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_time = models.IntegerField(help_text="Estimated time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'optimized_routes'

    def __str__(self):
        return f"Route {self.id} from {self.start_location}"

class RouteSegment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='segment_id')
    route = models.ForeignKey(OptimizedRoute, on_delete=models.CASCADE, related_name='segments')
    segment_order = models.IntegerField()
    x = models.DecimalField(max_digits=10, decimal_places=4)
    y = models.DecimalField(max_digits=10, decimal_places=4)
    z = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    class Meta:
        db_table = 'route_segments'
        ordering = ['segment_order']

    def __str__(self):
        return f"Segment {self.segment_order} for {self.route.id}"

class RouteHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='history_id')
    route = models.ForeignKey(OptimizedRoute, on_delete=models.CASCADE, related_name='history')
    executed_by = models.CharField(max_length=100, blank=True, null=True)  # could be user or robot id
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='PENDING')

    class Meta:
        db_table = 'route_history'

    def __str__(self):
        return f"History for {self.route.id} - {self.status}"
