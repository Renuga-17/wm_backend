from django.urls import path
from .presentation.api.storage_recommendation_view import StorageRecommendationView

urlpatterns = [
    path('', StorageRecommendationView.as_view(), name='storage-recommendation'),
]
