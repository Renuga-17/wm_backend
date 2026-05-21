from django.contrib import admin
from .models import Inbound

@admin.register(Inbound)
class InboundAdmin(admin.ModelAdmin):
    pass
