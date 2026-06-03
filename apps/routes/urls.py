import importlib.util
import pathlib
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .generate_route_view import GenerateRouteView

# Dynamically load RouteViewSet from the sibling views.py module to avoid import conflict with the views package
_views_path = pathlib.Path(__file__).resolve().parent / 'views.py'
_spec = importlib.util.spec_from_file_location('apps.routes.route_viewset', _views_path)
_route_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_route_module)
RouteViewSet = _route_module.RouteViewSet

router = DefaultRouter()
router.register(r'', RouteViewSet, basename='routes')

urlpatterns = [
    path('generate/', GenerateRouteView.as_view(), name='generate-route'),
    path('', include(router.urls)),
]
