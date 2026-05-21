from django.contrib import admin
from .models import Rack

@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    pass
