from rest_framework import serializers
from .models import OutboundShipment

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutboundShipment
        fields = '__all__'

