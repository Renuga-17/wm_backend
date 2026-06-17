from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, ScanLogViewSet

router = DefaultRouter()
router.register(r'scan-logs', ScanLogViewSet, basename='scan-logs')
router.register(r'', AuditLogViewSet, basename='audit_logs')

urlpatterns = [
    path('', include(router.urls)),
]

