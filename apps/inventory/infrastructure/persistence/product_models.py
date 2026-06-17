import uuid
from django.db import models

class ProductCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='category_id')
    category_name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'product_categories'

    def __str__(self):
        return self.category_name

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='product_id')
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, db_column='category_id', related_name='products')
    sku = models.CharField(max_length=100, unique=True)
    product_name = models.CharField(max_length=200)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    is_fragile = models.BooleanField(default=False)
    is_hazardous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return f"{self.product_name} ({self.sku})"

class ProductDimension(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='dimension_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id', related_name='dimensions')
    length = models.DecimalField(max_digits=10, decimal_places=2)
    width = models.DecimalField(max_digits=10, decimal_places=2)
    height = models.DecimalField(max_digits=10, decimal_places=2)
    box_length = models.DecimalField(max_digits=10, decimal_places=2)
    box_width = models.DecimalField(max_digits=10, decimal_places=2)
    box_height = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'product_dimensions'

    def __str__(self):
        return f"Dimensions for {self.product.product_name}"

class ProductStorageRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='rule_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id', related_name='storage_rules')
    allowed_zone_type = models.CharField(max_length=50)
    max_stack_height = models.IntegerField()
    required_temperature = models.DecimalField(max_digits=5, decimal_places=2)
    orientation_rule = models.CharField(max_length=100)

    class Meta:
        db_table = 'product_storage_rules'

    def __str__(self):
        return f"Storage Rule for {self.product.product_name}"

