from rest_framework import viewsets
from .models import Zone, ZoneBoundary
from .serializers import ZoneSerializer, ZoneBoundarySerializer

class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all().order_by('id')
    serializer_class = ZoneSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        
        # Optimize performance by pre-computing bulk lookup maps for list and retrieve actions
        if self.action in ['list', 'retrieve']:
            from apps.recommendations.models import CongestionPrediction, SlottingScore
            from apps.zones.models import WarehouseHeatmap
            from apps.bins.models import Bin
            from django.db import connection, transaction
            from django.db.models import Count, Q
            
            # 1. Congestion risk map
            if connection.vendor == 'postgresql':
                preds = CongestionPrediction.objects.order_by('zone', '-predicted_at').distinct('zone')
                pred_map = {pred.zone_id: float(pred.congestion_risk) for pred in preds}
            else:
                # Fallback for SQLite or other database engines
                preds = CongestionPrediction.objects.order_by('-predicted_at')
                pred_map = {}
                for pred in preds:
                    if pred.zone_id not in pred_map:
                        pred_map[pred.zone_id] = float(pred.congestion_risk)
            context['pred_map'] = pred_map

            # 2. Activity score map
            if connection.vendor == 'postgresql':
                heatmaps = WarehouseHeatmap.objects.order_by('zone', '-generated_at').distinct('zone')
                heatmap_map = {h.zone_id: float(h.activity_score) for h in heatmaps}
            else:
                # Fallback for SQLite or other database engines
                heatmaps = WarehouseHeatmap.objects.order_by('-generated_at')
                heatmap_map = {}
                for h in heatmaps:
                    if h.zone_id not in heatmap_map:
                        heatmap_map[h.zone_id] = float(h.activity_score)
            context['heatmap_map'] = heatmap_map

            # 3. Occupancy map
            bin_counts = Bin.objects.values('shelf__rack__zone_id').annotate(
                total=Count('id'),
                occupied=Count('id', filter=Q(is_occupied=True))
            )
            occupancy_map = {}
            for bc in bin_counts:
                zone_id = bc['shelf__rack__zone_id']
                if zone_id:
                    total = bc['total']
                    occupied = bc['occupied']
                    occupancy_map[zone_id] = round(occupied / total, 4) if total > 0 else 0.0
            context['occupancy_map'] = occupancy_map

            # 4. Slotting scores map
            scores = SlottingScore.objects.select_related('bin', 'product', 'bin__shelf__rack').order_by('-score')
            slotting_map = {}
            for s in scores:
                try:
                    zone_id = s.bin.shelf.rack.zone_id
                    if zone_id not in slotting_map:
                        slotting_map[zone_id] = []
                    if len(slotting_map[zone_id]) < 5:
                        slotting_map[zone_id].append({
                            "bin_code": s.bin.bin_code,
                            "product_sku": s.product.sku,
                            "score": float(s.score)
                        })
                except AttributeError:
                    continue
            context['slotting_map'] = slotting_map

        return context

class ZoneBoundaryViewSet(viewsets.ModelViewSet):
    queryset = ZoneBoundary.objects.all().order_by('id')
    serializer_class = ZoneBoundarySerializer


