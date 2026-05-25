import uuid
from django.db import models
from apps.products.models import Product

class Inventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='inventory_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id', related_name='inventory_records')
    total_quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    damaged_quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory'

    def __str__(self):
        return f"Inventory for {self.product.product_name}: {self.total_quantity}"

