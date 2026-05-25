from django.contrib import admin
from .models import OutboundShipment

@admin.register(OutboundShipment)
class OrderAdmin(admin.ModelAdmin):
    pass

