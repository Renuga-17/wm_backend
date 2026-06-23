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
<<<<<<< HEAD
        pred_map = self.context.get('pred_map')
        if pred_map is not None:
            return pred_map.get(obj.id, 0.10)
=======
        predictions_map = self.context.get('congestion_predictions')
        if predictions_map is not None:
            pred = predictions_map.get(obj.id)
            return float(pred.congestion_risk) if pred else 0.10
>>>>>>> aa8d66f5b9fd6bb95bb4e3703639135fd7dc4ec4
        pred = CongestionPrediction.objects.filter(zone=obj).order_by('-predicted_at').first()
        return float(pred.congestion_risk) if pred else 0.10

    def get_activity_score(self, obj):
<<<<<<< HEAD
        heatmap_map = self.context.get('heatmap_map')
        if heatmap_map is not None:
            return heatmap_map.get(obj.id, 0.0)
=======
        heatmaps_map = self.context.get('warehouse_heatmaps')
        if heatmaps_map is not None:
            heatmap = heatmaps_map.get(obj.id)
            return float(heatmap.activity_score) if heatmap else 0.0
>>>>>>> aa8d66f5b9fd6bb95bb4e3703639135fd7dc4ec4
        heatmap = WarehouseHeatmap.objects.filter(zone=obj).order_by('-generated_at').first()
        return float(heatmap.activity_score) if heatmap else 0.0

    def get_predictive_occupancy(self, obj):
<<<<<<< HEAD
        occupancy_map = self.context.get('occupancy_map')
        if occupancy_map is not None:
            return occupancy_map.get(obj.id, 0.0)
=======
        bin_counts_map = self.context.get('bin_counts')
        if bin_counts_map is not None:
            counts = bin_counts_map.get(obj.id)
            if counts:
                total = counts['total']
                occupied = counts['occupied']
                return round(occupied / total, 4) if total > 0 else 0.0
            return 0.0
>>>>>>> aa8d66f5b9fd6bb95bb4e3703639135fd7dc4ec4
        total = Bin.objects.filter(shelf__rack__zone=obj).count()
        occupied = Bin.objects.filter(shelf__rack__zone=obj, is_occupied=True).count()
        return round(occupied / total, 4) if total > 0 else 0.0

    def get_ai_slotting_scores(self, obj):
<<<<<<< HEAD
        slotting_map = self.context.get('slotting_map')
        if slotting_map is not None:
            return slotting_map.get(obj.id, [])
=======
        ai_slotting_scores_map = self.context.get('ai_slotting_scores')
        if ai_slotting_scores_map is not None:
            return ai_slotting_scores_map.get(obj.id, [])
>>>>>>> aa8d66f5b9fd6bb95bb4e3703639135fd7dc4ec4
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

