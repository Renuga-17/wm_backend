from rest_framework import serializers
from .models import Inbound

class InboundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inbound
        fields = '__all__'
