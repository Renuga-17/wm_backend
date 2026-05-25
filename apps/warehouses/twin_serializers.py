from rest_framework import serializers
from apps.bins.models import Shelf, Bin
from apps.zones.models import Zone, ZoneBoundary
from .models import Rack

class TwinBinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bin
        fields = ['id', 'bin_code', 'max_capacity', 'current_capacity', 'is_occupied']

class TwinShelfSerializer(serializers.ModelSerializer):
    bins = TwinBinSerializer(many=True, read_only=True)

    class Meta:
        model = Shelf
        fields = ['id', 'shelf_number', 'max_weight', 'height_from_ground', 'bins']

class TwinRackSerializer(serializers.ModelSerializer):
    shelves = TwinShelfSerializer(many=True, read_only=True)

    class Meta:
        model = Rack
        fields = [
            'id', 'rack_code', 'max_weight', 'x', 'y', 'z', 
            'width', 'height', 'depth', 'rotation_angle', 'shelves'
        ]

class TwinZoneBoundarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ZoneBoundary
        fields = ['id', 'polygon_points']

class TwinZoneSerializer(serializers.ModelSerializer):
    boundaries = TwinZoneBoundarySerializer(many=True, read_only=True)

    class Meta:
        model = Zone
        fields = [
            'id', 'zone_name', 'zone_type', 'x', 'y', 'z', 
            'width', 'height', 'depth', 'boundaries'
        ]
