from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .generate_route_view import GenerateRouteView
from .route_views import RouteViewSet

router = DefaultRouter()
router.register(r'', RouteViewSet, basename='routes')

urlpatterns = [
    path('generate/', GenerateRouteView.as_view(), name='generate-route'),
    path('', include(router.urls)),
]
