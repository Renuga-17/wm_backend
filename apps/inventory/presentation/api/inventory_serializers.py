from rest_framework import serializers
from apps.inventory.infrastructure.persistence.models import Inventory

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'
