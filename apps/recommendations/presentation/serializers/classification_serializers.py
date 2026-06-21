from rest_framework import serializers
from apps.recommendations.models.product_classification import ProductClassification

class ProductClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductClassification
        fields = ['id', 'product', 'movement_type', 'storage_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
