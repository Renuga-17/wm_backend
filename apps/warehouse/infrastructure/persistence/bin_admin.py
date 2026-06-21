from django.contrib import admin
from .models import Bin

@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    pass
