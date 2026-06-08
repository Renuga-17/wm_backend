from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.identity.presentation.api.user_urls')),
    path('api/audit-logs/', include('apps.identity.presentation.api.audit_urls')),
    
    path('api/layout/', include('apps.warehouse.presentation.api.layout_urls')),
    path('api/twin/', include('apps.warehouse.presentation.api.twin_urls')),
    path('api/warehouses/', include('apps.warehouse.presentation.api.warehouse_urls')),
    path('api/zones/', include('apps.warehouse.presentation.api.zone_urls')),
    path('api/bins/', include('apps.warehouse.presentation.api.bin_urls')),
    path('api/routes/', include('apps.warehouse.presentation.api.route_urls')),
    
    path('api/products/', include('apps.inventory.presentation.api.product_urls')),
    path('api/inventory/', include('apps.inventory.presentation.api.inventory_urls')),
    path('api/movements/', include('apps.inventory.presentation.api.movement_urls')),
    path('api/recommendations/', include('apps.inventory.presentation.api.recommendation_urls')),
    path('api/ai/', include('apps.inventory.presentation.api.ai_urls')),
    path('api/dashboards/', include('apps.inventory.presentation.api.dashboard_urls')),
    
    path('api/orders/', include('apps.orders.presentation.api.order_urls')),
    
    path('api/inbound/', include('apps.inbound.presentation.api.inbound_urls')),
    path('api/ocr/', include('apps.inbound.presentation.api.ocr_urls')),
]

from django.conf import settings
from django.conf.urls.static import static

# Serve media files in development / test
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

