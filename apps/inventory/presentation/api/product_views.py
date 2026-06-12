from rest_framework import viewsets
from apps.inventory.infrastructure.persistence.models import Product, ProductDimension, ProductStorageRule
from .serializers import ProductSerializer, ProductDimensionSerializer, ProductStorageRuleSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDimensionViewSet(viewsets.ModelViewSet):
    queryset = ProductDimension.objects.all().order_by('-id')
    serializer_class = ProductDimensionSerializer

class ProductStorageRuleViewSet(viewsets.ModelViewSet):
    queryset = ProductStorageRule.objects.all().order_by('-id')
    serializer_class = ProductStorageRuleSerializer

