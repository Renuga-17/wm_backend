from rest_framework import viewsets
from common.permissions import ReadOnlyOrAuthenticated
from apps.inventory.infrastructure.persistence.models import Product, ProductDimension, ProductStorageRule
from .serializers import ProductSerializer, ProductDimensionSerializer, ProductStorageRuleSerializer

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all().order_by('-id')
        sku = self.request.query_params.get('sku')
        if sku:
            queryset = queryset.filter(sku=sku)
        return queryset

class ProductDimensionViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = ProductDimension.objects.all().order_by('-id')
    serializer_class = ProductDimensionSerializer

class ProductStorageRuleViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = ProductStorageRule.objects.all().order_by('-id')
    serializer_class = ProductStorageRuleSerializer


