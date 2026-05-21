from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/warehouses/', include('apps.warehouses.urls')),
    path('api/zones/', include('apps.zones.urls')),
    path('api/racks/', include('apps.racks.urls')),
    path('api/bins/', include('apps.bins.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/inbound/', include('apps.inbound.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/movements/', include('apps.movements.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
    path('api/dashboards/', include('apps.dashboards.urls')),
    path('api/audit-logs/', include('apps.audit_logs.urls')),
]
