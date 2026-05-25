from rest_framework import serializers
from .models import OptimizedRoute, RouteSegment

class RouteSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteSegment
        fields = ['segment_order', 'x', 'y', 'z']

class OptimizedRouteSerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField()

    class Meta:
        model = OptimizedRoute
        fields = ['id', 'start_location', 'distance', 'estimated_time', 'path', 'created_at']

    def get_path(self, obj):
        segments = obj.segments.all().order_by('segment_order')
        return [[float(s.x), float(s.y)] for s in segments]

class RouteOptimizeRequestSerializer(serializers.Serializer):
    warehouse_id = serializers.UUIDField(required=True)
    start = serializers.CharField(max_length=100, required=True)
    targets = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        min_length=1
    )
