from rest_framework import serializers
from apps.inventory.infrastructure.persistence.models import Dashboard, RobotTask, RouteOptimization

class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = '__all__'

class RobotTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = RobotTask
        fields = '__all__'

class RouteOptimizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteOptimization
        fields = '__all__'

