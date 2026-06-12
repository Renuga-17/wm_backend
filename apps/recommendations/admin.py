from django.contrib import admin
from .models.recommendation_rule import RecommendationRule
from .models.product_classification import ProductClassification
from .models.storage_recommendation import StorageRecommendation
from .models.bin_allocation import BinAllocation
from .models.bin_3d_placement import Bin3DPlacement

@admin.register(RecommendationRule)
class RecommendationRuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'movement_type', 'storage_type', 'zone_group_type', 'priority')
    list_filter = ('movement_type', 'storage_type', 'zone_group_type')
    search_fields = ('description', 'zone_group_type')

@admin.register(ProductClassification)
class ProductClassificationAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'storage_type', 'created_at')
    list_filter = ('movement_type', 'storage_type')
    search_fields = ('product__sku', 'product__product_name')

@admin.register(StorageRecommendation)
class StorageRecommendationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'zone_group', 'zone', 'recommendation_score', 'recommendation_source', 'created_at')
    list_filter = ('recommendation_source', 'zone_group')
    search_fields = ('product__sku', 'recommendation_reason')

@admin.register(BinAllocation)
class BinAllocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'zone_group', 'zone', 'rack', 'shelf', 'bin', 'allocation_score', 'created_at')
    list_filter = ('allocation_source', 'zone_group')
    search_fields = ('product__sku', 'bin__bin_code', 'allocation_reason')

@admin.register(Bin3DPlacement)
class Bin3DPlacementAdmin(admin.ModelAdmin):
    list_display = ('id', 'bin_allocation', 'occupied_volume', 'remaining_volume', 'utilization_percentage', 'placement_strategy', 'label_direction', 'position_x', 'position_y', 'position_z')
    list_filter = ('placement_strategy', 'label_direction')
    search_fields = ('bin_allocation__bin__bin_code', 'bin_allocation__product__sku')


