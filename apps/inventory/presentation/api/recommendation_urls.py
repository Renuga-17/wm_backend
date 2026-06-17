from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecommendationViewSet
from apps.recommendations.presentation.api.bin_allocation_view import BinAllocationView
from apps.recommendations.presentation.api.three_d_placement_view import ThreeDPlacementView
from apps.recommendations.presentation.api.bin_allocation_complete_view import BinAllocationCompleteView

router = DefaultRouter()
router.register(r'', RecommendationViewSet, basename='recommendations')

urlpatterns = [
    path('storage/', include('apps.recommendations.urls')),
    path('bin-allocation/<int:pk>/complete/', BinAllocationCompleteView.as_view(), name='bin-allocation-complete'),
    path('bin-allocation/', BinAllocationView.as_view(), name='bin-allocation'),
    path('3d-placement/', ThreeDPlacementView.as_view(), name='three-d-placement'),
    path('', include(router.urls)),
]


