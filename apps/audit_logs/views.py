from rest_framework import viewsets
from .models import AuditLog, ScanLog
from .serializers import AuditLogSerializer, ScanLogSerializer

class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer

class ScanLogViewSet(viewsets.ModelViewSet):
    queryset = ScanLog.objects.all()
    serializer_class = ScanLogSerializer

