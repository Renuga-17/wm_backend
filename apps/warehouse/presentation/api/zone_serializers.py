from rest_framework import serializers
from apps.warehouse.infrastructure.persistence.models import Zone, ZoneBoundary, WarehouseHeatmap, ZoneGroup, Aisle
from apps.inventory.infrastructure.persistence.models import CongestionPrediction, SlottingScore
from apps.warehouse.infrastructure.persistence.models import Bin

class ZoneGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZoneGroup
        fields = '__all__'

class AisleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aisle
        fields = '__all__'

class ZoneSerializer(serializers.ModelSerializer):
    congestion_risk = serializers.SerializerMethodField()
    activity_score = serializers.SerializerMethodField()
    predictive_occupancy = serializers.SerializerMethodField()
    ai_slotting_scores = serializers.SerializerMethodField()

    class Meta:
        model = Zone
        fields = [
            'id', 'warehouse', 'zone_group', 'zone_name', 'zone_type', 
            'x', 'y', 'z', 'width', 'height', 'depth',
            'congestion_risk', 'activity_score', 'predictive_occupancy', 'ai_slotting_scores'
        ]

    def get_congestion_risk(self, obj):
        predictions_map = self.context.get('congestion_predictions')
        if predictions_map is not None:
            pred = predictions_map.get(obj.id)
            return float(pred.congestion_risk) if pred else 0.10
        pred = CongestionPrediction.objects.filter(zone=obj).order_by('-predicted_at').first()
        return float(pred.congestion_risk) if pred else 0.10

    def get_activity_score(self, obj):
        heatmaps_map = self.context.get('warehouse_heatmaps')
        if heatmaps_map is not None:
            heatmap = heatmaps_map.get(obj.id)
            return float(heatmap.activity_score) if heatmap else 0.0
        heatmap = WarehouseHeatmap.objects.filter(zone=obj).order_by('-generated_at').first()
        return float(heatmap.activity_score) if heatmap else 0.0

    def get_predictive_occupancy(self, obj):
        bin_counts_map = self.context.get('bin_counts')
        if bin_counts_map is not None:
            counts = bin_counts_map.get(obj.id)
            if counts:
                total = counts['total']
                occupied = counts['occupied']
                return round(occupied / total, 4) if total > 0 else 0.0
            return 0.0
        total = Bin.objects.filter(shelf__rack__zone=obj).count()
        occupied = Bin.objects.filter(shelf__rack__zone=obj, is_occupied=True).count()
        return round(occupied / total, 4) if total > 0 else 0.0

    def get_ai_slotting_scores(self, obj):
        ai_slotting_scores_map = self.context.get('ai_slotting_scores')
        if ai_slotting_scores_map is not None:
            return ai_slotting_scores_map.get(obj.id, [])
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

