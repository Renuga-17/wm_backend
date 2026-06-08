from rest_framework import serializers

class RouteGenerateRequestSerializer(serializers.Serializer):
    source_bin_id = serializers.UUIDField(required=True, help_text="Source Bin UUID")
    destination_bin_id = serializers.UUIDField(required=True, help_text="Destination Bin UUID")
