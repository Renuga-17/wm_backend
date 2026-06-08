from rest_framework import serializers
from apps.inventory.infrastructure.persistence.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
