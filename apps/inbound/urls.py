from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InboundViewSet

router = DefaultRouter()
router.register(r'', InboundViewSet, basename='inbound')

urlpatterns = [
    path('', include(router.urls)),
]
