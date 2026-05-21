from rest_framework import viewsets
from .models import Dashboard
from .serializers import DashboardSerializer

class DashboardViewSet(viewsets.ModelViewSet):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
