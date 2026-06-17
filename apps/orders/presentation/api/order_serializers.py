from rest_framework import serializers
from apps.orders.infrastructure.persistence.models import OutboundShipment

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutboundShipment
        fields = '__all__'

