from rest_framework import serializers
from apps.inventory.infrastructure.persistence.models import Recommendation, AllocationRecommendation, DemandForecast, CongestionPrediction, SlottingScore, AIDecision, SystemAlert

class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'


class DemandForecastSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_name = serializers.CharField(source='product.product_name', read_only=True)

    class Meta:
        model = DemandForecast
        fields = ['id', 'product', 'product_sku', 'product_name', 'predicted_demand_score', 'forecast_period', 'confidence_score', 'forecasted_at']


class CongestionPredictionSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.zone_name', read_only=True)

    class Meta:
        model = CongestionPrediction
        fields = ['id', 'zone', 'zone_name', 'congestion_risk', 'predicted_traffic_volume', 'predicted_at']


class AIDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIDecision
        fields = '__all__'


class SystemAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemAlert
        fields = '__all__'

