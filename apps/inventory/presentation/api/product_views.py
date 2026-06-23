from rest_framework import viewsets
from common.permissions import ReadOnlyOrAuthenticated
from apps.inventory.infrastructure.persistence.models import Product, ProductDimension, ProductStorageRule
from .serializers import ProductSerializer, ProductDimensionSerializer, ProductStorageRuleSerializer

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDimensionViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = ProductDimension.objects.all().order_by('-id')
    serializer_class = ProductDimensionSerializer

class ProductStorageRuleViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = ProductStorageRule.objects.all().order_by('-id')
    serializer_class = ProductStorageRuleSerializer


