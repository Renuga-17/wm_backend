from django.urls import path
from .layout_views import (
    LayoutUploadView,
    LayoutDetailView,
    LayoutAnalyzeView,
    LayoutEntitiesView,
    GenerateTopologyView,
    LayoutGraphView
)

urlpatterns = [
    path('upload', LayoutUploadView.as_view(), name='layout-upload'),
    path('analyze', LayoutAnalyzeView.as_view(), name='layout-analyze'),
    path('entities', LayoutEntitiesView.as_view(), name='layout-entities'),
    path('generate-topology', GenerateTopologyView.as_view(), name='layout-generate-topology'),
    path('graph', LayoutGraphView.as_view(), name='layout-graph'),
    path('<uuid:layout_id>', LayoutDetailView.as_view(), name='layout-detail'),
]
