from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet, RobotTaskViewSet, RouteOptimizationViewSet, AnalyticsViewSet

router = DefaultRouter()
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'robot-tasks', RobotTaskViewSet, basename='robot-tasks')
router.register(r'route-optimizations', RouteOptimizationViewSet, basename='route-optimizations')
router.register(r'', DashboardViewSet, basename='dashboards')

urlpatterns = [
    path('', include(router.urls)),
]

