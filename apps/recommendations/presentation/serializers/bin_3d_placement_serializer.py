from rest_framework import serializers
from ...models.bin_3d_placement import Bin3DPlacement

class Bin3DPlacementSerializer(serializers.ModelSerializer):
    selected_orientation = serializers.CharField(source='bin_allocation.selected_orientation', read_only=True)
    bin_code = serializers.CharField(source='bin_allocation.bin.bin_code', read_only=True)

    class Meta:
        model = Bin3DPlacement
        fields = [
            'id',
            'bin_allocation',
            'bin_code',
            'occupied_volume',
            'remaining_volume',
            'utilization_percentage',
            'placement_strategy',
            'label_direction',
            'position_x',
            'position_y',
            'position_z',
            'selected_orientation',
            'created_at'
        ]
        read_only_fields = ['id', 'bin_allocation', 'created_at']
