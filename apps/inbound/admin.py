from django.contrib import admin
from .models import InboundShipment

@admin.register(InboundShipment)
class InboundAdmin(admin.ModelAdmin):
    pass

