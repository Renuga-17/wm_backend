from rest_framework import viewsets
from apps.recommendations.models.product_classification import ProductClassification
from ..serializers.classification_serializers import ProductClassificationSerializer

class ProductClassificationViewSet(viewsets.ModelViewSet):
    queryset = ProductClassification.objects.all().order_by('-id')
    serializer_class = ProductClassificationSerializer
