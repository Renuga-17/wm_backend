from django.contrib import admin
from .models import StockMovement, StorageAllocation

@admin.register(StockMovement)
class MovementAdmin(admin.ModelAdmin):
    pass

@admin.register(StorageAllocation)
class StorageAllocationAdmin(admin.ModelAdmin):
    pass

