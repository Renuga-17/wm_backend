from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ZoneViewSet, ZoneBoundaryViewSet

router = DefaultRouter()
router.register(r'boundaries', ZoneBoundaryViewSet, basename='zone-boundaries')
router.register(r'', ZoneViewSet, basename='zones')

urlpatterns = [
    path('', include(router.urls)),
]

