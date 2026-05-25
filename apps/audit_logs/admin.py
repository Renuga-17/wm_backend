from django.contrib import admin
from .models import ScanLog, AuditLog

@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    pass

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    pass

