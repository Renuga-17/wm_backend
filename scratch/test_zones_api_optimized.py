import os
import sys
import django
import time

sys.path.append(r"c:\TYN\wm_backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.warehouse.infrastructure.persistence.models import Zone
from apps.warehouse.presentation.api.zone_serializers import ZoneSerializer
from django.db import connection, reset_queries

# Optimized logic
from apps.inventory.infrastructure.persistence.models import CongestionPrediction, SlottingScore
from apps.warehouse.infrastructure.persistence.models import WarehouseHeatmap, Bin
from django.db.models import Count, Q

def get_optimized_context():
    context = {}
    
    # 1. Fetch latest CongestionPrediction per zone
    if connection.vendor == 'postgresql':
        predictions = CongestionPrediction.objects.order_by('zone_id', '-predicted_at').distinct('zone_id')
        context['congestion_predictions'] = {p.zone_id: p for p in predictions}
    else:
        predictions_all = CongestionPrediction.objects.order_by('-predicted_at')
        predictions = {}
        for p in predictions_all:
            if p.zone_id not in predictions:
                predictions[p.zone_id] = p
        context['congestion_predictions'] = predictions

    # 2. Fetch latest WarehouseHeatmap per zone
    if connection.vendor == 'postgresql':
        heatmaps = WarehouseHeatmap.objects.order_by('zone_id', '-generated_at').distinct('zone_id')
        context['warehouse_heatmaps'] = {h.zone_id: h for h in heatmaps}
    else:
        heatmaps_all = WarehouseHeatmap.objects.order_by('-generated_at')
        heatmaps = {}
        for h in heatmaps_all:
            if h.zone_id not in heatmaps:
                heatmaps[h.zone_id] = h
        context['warehouse_heatmaps'] = heatmaps

    # 3. Aggregate bin counts per zone
    bin_counts = Bin.objects.filter(shelf__rack__zone__isnull=False).values('shelf__rack__zone_id').annotate(
        total=Count('id'),
        occupied=Count('id', filter=Q(is_occupied=True))
    )
    context['bin_counts'] = {b['shelf__rack__zone_id']: b for b in bin_counts}

    # 4. Fetch slotting scores
    slotting_scores_dict = {}
    scores = SlottingScore.objects.select_related('bin', 'product', 'bin__shelf__rack').order_by('-score')
    for s in scores:
        if not s.bin or not s.bin.shelf or not s.bin.shelf.rack:
            continue
        zone_id = s.bin.shelf.rack.zone_id
        if zone_id not in slotting_scores_dict:
            slotting_scores_dict[zone_id] = []
        if len(slotting_scores_dict[zone_id]) < 5:
            slotting_scores_dict[zone_id].append({
                "bin_code": s.bin.bin_code,
                "product_sku": s.product.sku,
                "score": float(s.score)
            })
    context['ai_slotting_scores'] = slotting_scores_dict
    
    return context

# Modify ZoneSerializer dynamically to support context
original_get_congestion_risk = ZoneSerializer.get_congestion_risk
original_get_activity_score = ZoneSerializer.get_activity_score
original_get_predictive_occupancy = ZoneSerializer.get_predictive_occupancy
original_get_ai_slotting_scores = ZoneSerializer.get_ai_slotting_scores

def new_get_congestion_risk(self, obj):
    predictions_map = self.context.get('congestion_predictions')
    if predictions_map is not None:
        pred = predictions_map.get(obj.id)
        return float(pred.congestion_risk) if pred else 0.10
    return original_get_congestion_risk(self, obj)

def new_get_activity_score(self, obj):
    heatmaps_map = self.context.get('warehouse_heatmaps')
    if heatmaps_map is not None:
        heatmap = heatmaps_map.get(obj.id)
        return float(heatmap.activity_score) if heatmap else 0.0
    return original_get_activity_score(self, obj)

def new_get_predictive_occupancy(self, obj):
    bin_counts_map = self.context.get('bin_counts')
    if bin_counts_map is not None:
        counts = bin_counts_map.get(obj.id)
        if counts:
            total = counts['total']
            occupied = counts['occupied']
            return round(occupied / total, 4) if total > 0 else 0.0
        return 0.0
    return original_get_predictive_occupancy(self, obj)

def new_get_ai_slotting_scores(self, obj):
    ai_slotting_scores_map = self.context.get('ai_slotting_scores')
    if ai_slotting_scores_map is not None:
        return ai_slotting_scores_map.get(obj.id, [])
    return original_get_ai_slotting_scores(self, obj)

ZoneSerializer.get_congestion_risk = new_get_congestion_risk
ZoneSerializer.get_activity_score = new_get_activity_score
ZoneSerializer.get_predictive_occupancy = new_get_predictive_occupancy
ZoneSerializer.get_ai_slotting_scores = new_get_ai_slotting_scores

reset_queries()
t0 = time.time()
zones = Zone.objects.all().order_by('id')
ctx = get_optimized_context()
serializer = ZoneSerializer(zones, many=True, context=ctx)
data = serializer.data
t1 = time.time()

print(f"Optimized: Serialized {len(data)} zones in {t1 - t0:.2f} seconds.")
print(f"Number of SQL queries executed: {len(connection.queries)}")
for q in connection.queries:
    print(f"SQL: {q['sql']}\nTime: {q['time']}\n")
