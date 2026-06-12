import uuid
from django.db import models
from .warehouse_models import Rack


class Shelf(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='shelf_id')
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE, db_column='rack_id', related_name='shelves')
    shelf_number = models.IntegerField()
    max_weight = models.DecimalField(max_digits=10, decimal_places=2)
    height_from_ground = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'shelves'

    def __str__(self):
        return f"Shelf {self.shelf_number} on {self.rack.rack_code}"

class Bin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='bin_id')
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, db_column='shelf_id', related_name='bins')
    bin_code = models.CharField(max_length=50, unique=True)
    max_capacity = models.DecimalField(max_digits=10, decimal_places=2)
    current_capacity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    length = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    width  = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    height = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_occupied = models.BooleanField(default=False)

    class Meta:
        db_table = 'bins'

    def __str__(self):
        return self.bin_code
