import uuid
from django.db import models
from .product_models import Product
from apps.warehouse.infrastructure.persistence.models import Bin

class AIModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='model_id')
    model_name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=50)
    accuracy = models.DecimalField(max_digits=5, decimal_places=4)
    deployed_at = models.DateTimeField()

    class Meta:
        db_table = 'ai_models'

    def __str__(self):
        return f"{self.model_name} ({self.model_version})"

class AIPrediction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='prediction_id')
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, db_column='model_id', related_name='predictions')
    prediction_type = models.CharField(max_length=100)
    prediction_result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_predictions'

    def __str__(self):
        return f"Prediction {self.id} ({self.prediction_type})"

class AllocationRecommendation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='recommendation_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id', related_name='recommendations')
    recommended_bin = models.ForeignKey(Bin, on_delete=models.CASCADE, db_column='recommended_bin', related_name='recommendations')
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4)
    reasoning = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'allocation_recommendations'

    def __str__(self):
        return f"Recommendation for {self.product.product_name} -> {self.recommended_bin.bin_code}"

# Backward compatibility alias
Recommendation = AllocationRecommendation


class DemandForecast(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='forecast_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='demand_forecasts')
    predicted_demand_score = models.DecimalField(max_digits=5, decimal_places=4)  # 0.0 to 1.0
    forecast_period = models.CharField(max_length=50, default='DAILY')
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.90)
    forecasted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'demand_forecasts'

    def __str__(self):
        return f"Forecast {self.product.sku}: {self.predicted_demand_score}"


class CongestionPrediction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='prediction_id')
    zone = models.ForeignKey('warehouse.Zone', on_delete=models.CASCADE, related_name='congestion_predictions')
    congestion_risk = models.DecimalField(max_digits=5, decimal_places=4)  # 0.0 to 1.0
    predicted_traffic_volume = models.IntegerField(default=0)
    predicted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'congestion_predictions'

    def __str__(self):
        return f"Congestion Risk {self.zone.zone_name}: {self.congestion_risk}"


class SlottingScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='score_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    bin = models.ForeignKey(Bin, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=10, decimal_places=4)
    congestion_penalty = models.DecimalField(max_digits=10, decimal_places=4, default=0.0)
    travel_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0.0)
    affinity_bonus = models.DecimalField(max_digits=10, decimal_places=4, default=0.0)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'slotting_scores'

    def __str__(self):
        return f"Slotting Score {self.product.sku} -> {self.bin.bin_code}: {self.score}"


class SlottingHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='history_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    source_bin = models.ForeignKey(Bin, on_delete=models.CASCADE, null=True, related_name='slotting_source_history')
    target_bin = models.ForeignKey(Bin, on_delete=models.CASCADE, related_name='slotting_target_history')
    moved_at = models.DateTimeField(auto_now_add=True)
    pick_time_seconds = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    efficiency_gain = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = 'slotting_history'

    def __str__(self):
        return f"Slotting Move {self.product.sku} -> {self.target_bin.bin_code}"


class AIDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='decision_id')
    decision_type = models.CharField(max_length=100)  # PLACEMENT, RESLOTTING, HOTSPOT_PREVENTION
    input_features = models.JSONField(default=dict)
    decision_output = models.JSONField(default=dict)
    feedback_received = models.JSONField(null=True, blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_decisions'

    def __str__(self):
        return f"AI Decision {self.decision_type} ({self.executed_at})"


class SystemAlert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='alert_id')
    alert_type = models.CharField(max_length=50) # CONGESTION, OVERUTILIZED_RACK, DEAD_STOCK, LOW_THROUGHPUT, INEFFICIENT_ROUTING
    zone_code = models.CharField(max_length=50, null=True, blank=True)
    severity = models.CharField(max_length=20, default='INFO') # INFO, WARNING, CRITICAL
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'system_alerts'

    def __str__(self):
        return f"Alert {self.alert_type} ({self.severity}) at {self.created_at}"


