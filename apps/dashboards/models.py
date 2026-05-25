import uuid
from django.db import models

class RobotTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='task_id')
    task_type = models.CharField(max_length=100)
    source_location = models.CharField(max_length=100)
    destination_location = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'robot_tasks'

    def __str__(self):
        return f"Robot Task {self.id} ({self.task_type})"

class RouteOptimization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='route_id')
    source_location = models.CharField(max_length=100)
    destination_location = models.CharField(max_length=100)
    optimized_path = models.JSONField()
    estimated_time = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'route_optimizations'

    def __str__(self):
        return f"Route {self.id}: {self.source_location} -> {self.destination_location}"

# Keep placeholder class to avoid import breakages
class Dashboard(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        managed = False

