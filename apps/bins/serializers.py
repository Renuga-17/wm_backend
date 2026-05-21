from rest_framework import serializers
from .models import Bin

class BinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bin
        fields = '__all__'
