from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InboundViewSet
from .putaway_views import PutawayTaskViewSet

router = DefaultRouter()
router.register(r'putaway', PutawayTaskViewSet, basename='putaway')
router.register(r'', InboundViewSet, basename='inbound')

urlpatterns = [
    path('', include(router.urls)),
]
