import uuid
from django.db import models
from .product_models import Product
from apps.warehouse.infrastructure.persistence.models import Bin

class StockMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='movement_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id', related_name='stock_movements')
    from_bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True, db_column='from_bin', related_name='movements_from')
    to_bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True, db_column='to_bin', related_name='movements_to')
    quantity = models.IntegerField()
    movement_type = models.CharField(max_length=50)
    moved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_movements'

    def __str__(self):
        return f"Movement {self.id}: {self.product.product_name} ({self.quantity})"

class StorageAllocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='allocation_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id', related_name='allocations')
    bin = models.ForeignKey(Bin, on_delete=models.CASCADE, db_column='bin_id', related_name='allocations')
    quantity = models.IntegerField()
    allocated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'storage_allocations'

    def __str__(self):
        return f"Allocation {self.id}: {self.product.product_name} in {self.bin.bin_code}"

