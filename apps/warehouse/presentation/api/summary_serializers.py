from rest_framework import serializers

class TwinSummarySerializer(serializers.Serializer):
    total_warehouses = serializers.IntegerField()
    total_zones = serializers.IntegerField()
    total_racks = serializers.IntegerField()
    total_bins = serializers.IntegerField()
    occupancy_percentage = serializers.FloatField()
    navigation_node_count = serializers.IntegerField()
    navigation_edge_count = serializers.IntegerField()
