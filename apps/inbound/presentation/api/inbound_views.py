from rest_framework import viewsets
from apps.inbound.infrastructure.persistence.models import InboundShipment
from .serializers import InboundSerializer

class InboundViewSet(viewsets.ModelViewSet):
    serializer_class = InboundSerializer

    def get_queryset(self):
        return InboundShipment.objects.all().select_related(
            'ocr_document'
        ).prefetch_related(
            'line_items',
            'line_items__product',
            'line_items__bin_allocations'
        ).order_by('-expected_arrival', '-id')

