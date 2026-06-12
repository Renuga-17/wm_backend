from rest_framework import serializers
from ...models.storage_recommendation import StorageRecommendation

class StorageRecommendationInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=True)

class StorageRecommendationOutputSerializer(serializers.ModelSerializer):
    zone_group = serializers.CharField(source='zone_group.code')
    zone = serializers.CharField(source='zone.zone_name')

    class Meta:
        model = StorageRecommendation
        fields = [
            'zone_group',
            'zone',
            'recommendation_reason',
            'recommendation_score',
            'recommendation_source',
            'recommendation_version'
        ]
