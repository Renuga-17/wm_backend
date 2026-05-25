from rest_framework import serializers
from .models import InboundShipment

class InboundSerializer(serializers.ModelSerializer):
    class Meta:
        model = InboundShipment
        fields = '__all__'
