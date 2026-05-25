from django.urls import path
from .twin_views import (
    WarehouseTwinDetailView, TwinRacksView, TwinZonesView,
    TwinOccupancyView, TwinPathsView
)

urlpatterns = [
    path('layout/<uuid:layout_id>', WarehouseTwinDetailView.as_view(), name='twin-layout-detail'),
    path('racks', TwinRacksView.as_view(), name='twin-racks'),
    path('zones', TwinZonesView.as_view(), name='twin-zones'),
    path('occupancy', TwinOccupancyView.as_view(), name='twin-occupancy'),
    path('paths', TwinPathsView.as_view(), name='twin-paths'),
]
