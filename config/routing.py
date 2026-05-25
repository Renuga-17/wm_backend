from django.urls import re_path
from apps.warehouses.consumers import OccupancyConsumer
from apps.routes.consumers import RouteConsumer
from apps.recommendations.consumers import (
    RecommendationConsumer, CongestionConsumer, SlottingConsumer, AlertConsumer
)
from apps.inventory.consumers import InventoryConsumer

websocket_urlpatterns = [
    re_path(r'ws/occupancy/$', OccupancyConsumer.as_asgi()),
    re_path(r'ws/routes/$', RouteConsumer.as_asgi()),
    re_path(r'ws/recommendations/$', RecommendationConsumer.as_asgi()),
    re_path(r'ws/inventory/$', InventoryConsumer.as_asgi()),
    re_path(r'ws/congestion/$', CongestionConsumer.as_asgi()),
    re_path(r'ws/slotting/$', SlottingConsumer.as_asgi()),
    re_path(r'ws/alerts/$', AlertConsumer.as_asgi()),
]
