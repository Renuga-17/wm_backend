from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BinViewSet

router = DefaultRouter()
router.register(r'', BinViewSet, basename='bins')

urlpatterns = [
    path('', include(router.urls)),
]
