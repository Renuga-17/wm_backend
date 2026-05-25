from django.urls import path
from .layout_views import LayoutUploadView, LayoutDetailView, LayoutAnalyzeView, LayoutEntitiesView

urlpatterns = [
    path('upload', LayoutUploadView.as_view(), name='layout-upload'),
    path('analyze', LayoutAnalyzeView.as_view(), name='layout-analyze'),
    path('entities', LayoutEntitiesView.as_view(), name='layout-entities'),
    path('<uuid:layout_id>', LayoutDetailView.as_view(), name='layout-detail'),
]
