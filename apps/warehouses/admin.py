from django.contrib import admin
from .models import Warehouse, Rack

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('id', 'name')

@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    pass


