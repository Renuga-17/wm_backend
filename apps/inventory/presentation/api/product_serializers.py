from rest_framework import serializers
from apps.inventory.infrastructure.persistence.models import Product, ProductDimension, ProductStorageRule

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class ProductDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDimension
        fields = ['id', 'product', 'length', 'width', 'height', 'box_length', 'box_width', 'box_height']
        read_only_fields = ['id']

    def validate(self, data):
        dimension_fields = ['length', 'width', 'height', 'box_length', 'box_width', 'box_height']
        for field in dimension_fields:
            if field in data:
                val = data[field]
                if val is not None and val <= 0:
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').capitalize()} must be a positive value greater than 0."})
        return data

class ProductStorageRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStorageRule
        fields = ['id', 'product', 'allowed_zone_type', 'max_stack_height', 'required_temperature', 'orientation_rule']
        read_only_fields = ['id']

