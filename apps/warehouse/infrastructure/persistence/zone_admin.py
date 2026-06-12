from django.contrib import admin
from .models import Zone, ZoneGroup, Aisle

@admin.register(ZoneGroup)
class ZoneGroupAdmin(admin.ModelAdmin):
    pass

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    pass

@admin.register(Aisle)
class AisleAdmin(admin.ModelAdmin):
    pass
