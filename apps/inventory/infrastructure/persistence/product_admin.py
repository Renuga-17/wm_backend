from django.contrib import admin
from .models import Product, ProductDimension, ProductStorageRule

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku', 'product_name', 'category', 'weight', 'is_fragile', 'is_hazardous')
    search_fields = ('sku', 'product_name')
    list_filter = ('category', 'is_fragile', 'is_hazardous')

@admin.register(ProductDimension)
class ProductDimensionAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'length', 'width', 'height', 'box_length', 'box_width', 'box_height')
    search_fields = ('product__sku', 'product__product_name')

@admin.register(ProductStorageRule)
class ProductStorageRuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'allowed_zone_type', 'max_stack_height', 'required_temperature', 'orientation_rule')
    search_fields = ('product__sku', 'product__product_name')

