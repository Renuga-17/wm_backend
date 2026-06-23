from rest_framework import serializers
from apps.inbound.infrastructure.persistence.models import InboundShipment

class InboundSerializer(serializers.ModelSerializer):
    class Meta:
        model = InboundShipment
        fields = '__all__'
