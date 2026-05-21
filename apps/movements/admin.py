from django.contrib import admin
from .models import Movement

@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    pass
