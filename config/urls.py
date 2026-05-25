from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/layout/', include('apps.warehouses.layout_urls')),
    path('api/twin/', include('apps.warehouses.twin_urls')),
    path('api/warehouses/', include('apps.warehouses.urls')),
    path('api/zones/', include('apps.zones.urls')),
    path('api/bins/', include('apps.bins.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/inbound/', include('apps.inbound.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/movements/', include('apps.movements.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
    path('api/ai/', include('apps.recommendations.ai_urls')),
    path('api/dashboards/', include('apps.dashboards.urls')),
    path('api/audit-logs/', include('apps.audit_logs.urls')),
    path('api/routes/', include('apps.routes.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

# Serve media files in development / test
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

