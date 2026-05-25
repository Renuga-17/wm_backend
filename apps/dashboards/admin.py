from django.contrib import admin
from .models import RobotTask, RouteOptimization

@admin.register(RobotTask)
class RobotTaskAdmin(admin.ModelAdmin):
    pass

@admin.register(RouteOptimization)
class RouteOptimizationAdmin(admin.ModelAdmin):
    pass

