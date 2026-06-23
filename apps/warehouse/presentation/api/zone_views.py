from rest_framework import viewsets
from apps.warehouse.infrastructure.persistence.models import Zone, ZoneBoundary, ZoneGroup, Aisle
from .serializers import ZoneSerializer, ZoneBoundarySerializer, ZoneGroupSerializer, AisleSerializer

class ZoneGroupViewSet(viewsets.ModelViewSet):
    queryset = ZoneGroup.objects.all().order_by('id')
    serializer_class = ZoneGroupSerializer

class AisleViewSet(viewsets.ModelViewSet):
    queryset = Aisle.objects.all().order_by('id')
    serializer_class = AisleSerializer
from apps.inventory.infrastructure.persistence.models import CongestionPrediction, SlottingScore
from apps.warehouse.infrastructure.persistence.models import WarehouseHeatmap, Bin
from django.db.models import Count, Q
from django.db import connection

class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all().order_by('id')
    serializer_class = ZoneSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        
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

class ZoneBoundaryViewSet(viewsets.ModelViewSet):
    queryset = ZoneBoundary.objects.all().order_by('id')
    serializer_class = ZoneBoundarySerializer


