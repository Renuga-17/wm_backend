from rest_framework import serializers
from apps.warehouse.infrastructure.persistence.models import Bin

class BinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bin
        fields = '__all__'

    def validate(self, attrs):
        dimension_fields = ['length', 'width', 'height']
        for field in dimension_fields:
            if field in attrs:
                val = attrs[field]
                if val is not None and val <= 0:
                    raise serializers.ValidationError({field: f"{field.capitalize()} must be a positive value greater than 0."})
        return attrs
