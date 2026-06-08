from rest_framework import serializers
from apps.warehouse.infrastructure.persistence.models import Zone, ZoneBoundary, WarehouseHeatmap
from apps.inventory.infrastructure.persistence.models import CongestionPrediction, SlottingScore
from apps.warehouse.infrastructure.persistence.models import Bin

class ZoneSerializer(serializers.ModelSerializer):
    congestion_risk = serializers.SerializerMethodField()
    activity_score = serializers.SerializerMethodField()
    predictive_occupancy = serializers.SerializerMethodField()
    ai_slotting_scores = serializers.SerializerMethodField()

    class Meta:
        model = Zone
        fields = [
            'id', 'warehouse', 'zone_name', 'zone_type', 
            'x', 'y', 'z', 'width', 'height', 'depth',
            'congestion_risk', 'activity_score', 'predictive_occupancy', 'ai_slotting_scores'
        ]

    def get_congestion_risk(self, obj):
        pred = CongestionPrediction.objects.filter(zone=obj).order_by('-predicted_at').first()
        return float(pred.congestion_risk) if pred else 0.10

    def get_activity_score(self, obj):
        heatmap = WarehouseHeatmap.objects.filter(zone=obj).order_by('-generated_at').first()
        return float(heatmap.activity_score) if heatmap else 0.0

    def get_predictive_occupancy(self, obj):
        total = Bin.objects.filter(shelf__rack__zone=obj).count()
        occupied = Bin.objects.filter(shelf__rack__zone=obj, is_occupied=True).count()
        return round(occupied / total, 4) if total > 0 else 0.0

    def get_ai_slotting_scores(self, obj):
        scores = SlottingScore.objects.filter(bin__shelf__rack__zone=obj).select_related('bin', 'product').order_by('-score')[:5]
        return [
            {
                "bin_code": s.bin.bin_code,
                "product_sku": s.product.sku,
                "score": float(s.score)
            }
            for s in scores
        ]

class ZoneBoundarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ZoneBoundary
        fields = '__all__'

