import uuid
from django.db import models
from apps.products.models import Product
from django.conf import settings

class ScanLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='scan_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id', related_name='scan_logs')
    scan_type = models.CharField(max_length=50)
    scanned_location = models.CharField(max_length=100)
    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scan_logs'

    def __str__(self):
        return f"Scan {self.id} for {self.product.product_name}"

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='log_id')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_id', related_name='audit_logs')
    action_type = models.CharField(max_length=100)
    table_name = models.CharField(max_length=100)
    record_id = models.UUIDField()
    action_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'

    def __str__(self):
        return f"AuditLog {self.id}: {self.action_type} on {self.table_name}"

