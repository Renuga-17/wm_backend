import logging
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.inventory.infrastructure.persistence.models import Recommendation, AllocationRecommendation, DemandForecast, CongestionPrediction, AIDecision, SystemAlert
from .serializers import (
    RecommendationSerializer, DemandForecastSerializer, CongestionPredictionSerializer, 
    AIDecisionSerializer, SystemAlertSerializer
)
from apps.inventory.infrastructure.persistence.models import Product
from apps.warehouse.infrastructure.persistence.models import Bin
from apps.warehouse.infrastructure.persistence.models import WarehouseLayout
from integrations.ai_service_client import AIServiceClient
from apps.inventory.application.ai.ml_slotting import AISlottingEngine
from apps.inventory.application.ai.hotspot_prevention import HotspotPreventionEngine
from apps.inventory.application.services.slotting_service import SlottingService
from django.db import transaction
from apps.inventory.infrastructure.persistence.models import StorageAllocation
from apps.inventory.application.ai.feedback_loop import AIFeedbackLoop
from apps.inventory.application.ai.operational_scoring import OperationalScoringEngine
from decimal import Decimal

logger = logging.getLogger(__name__)

class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer

    @action(detail=False, methods=['post'], url_path='suggest-bin')
    def suggest_bin(self, request):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        inbound_id = request.data.get('inbound_id')

        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except (Product.DoesNotExist, ValueError):
            # Try finding by SKU
            product = Product.objects.filter(sku=product_id).first()
            if not product:
                return Response({"error": f"Product not found for ID or SKU: {product_id}"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Resolve warehouse_id
            layout = WarehouseLayout.objects.first()
            warehouse_id = layout.warehouse_id if layout else None
            if not warehouse_id:
                from apps.warehouse.infrastructure.persistence.models import Warehouse
                warehouse = Warehouse.objects.first()
                warehouse_id = warehouse.id if warehouse else None

            if not warehouse_id:
                raise ValueError("No warehouse or warehouse layout configured in system")

            # Invoke local AI slotting calculation
            recommendation = AISlottingEngine.optimize_slotting(product.id, warehouse_id)
            bin_obj = recommendation.recommended_bin
            confidence = float(recommendation.confidence_score)
            reasoning_text = recommendation.reasoning.get("logic", "AI optimized location.")
            
            logger.info("Local AI recommendation used")
        except Exception as e:
            # Local database fallback
            bin_obj = Bin.objects.filter(is_occupied=False).first() or Bin.objects.first()
            if not bin_obj:
                return Response({"error": "No available bins found in warehouse"}, status=status.HTTP_404_NOT_FOUND)
            
            confidence = 0.0
            reasoning_text = f"Fallback due to AI Service unavailability (local calculation failed: {str(e)})"
            
            recommendation = AllocationRecommendation.objects.create(
                product=product,
                recommended_bin=bin_obj,
                confidence_score=Decimal(str(confidence)),
                reasoning={"logic": reasoning_text}
            )
            
            logger.info("Fallback recommendation used")

        return Response({
            "success": True,
            "recommended_bin_id": str(bin_obj.id),
            "confidence_score": float(confidence),
            "reasoning": reasoning_text
        })

    @action(detail=False, methods=['post'], url_path='allocate')
    def allocate(self, request):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')

        if not product_id or quantity is None:
            return Response({"error": "product_id and quantity are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({"error": "Quantity must be > 0"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Quantity must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate product exists
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Smart slotting recommendation
        try:
            allocation_data = SlottingService.recommend_storage_location(product_id, quantity)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Validate recommended bin exists
        try:
            bin_obj = Bin.objects.get(id=allocation_data['bin'])
        except Bin.DoesNotExist:
            return Response({"error": "Recommended bin not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create allocation atomically
        with transaction.atomic():
            allocation = StorageAllocation.objects.create(
                product=product,
                bin=bin_obj,
                quantity=quantity
            )
            self.update_bin_occupancy(bin_obj, quantity)

        return Response({
            "allocation_id": str(allocation.id),
            "product_id": str(product.id),
            "zone": allocation_data['zone'],
            "rack": allocation_data['rack'],
            "shelf": allocation_data['shelf'],
            "bin": allocation_data['bin'],
            "quantity": quantity
        }, status=status.HTTP_201_CREATED)

    def update_bin_occupancy(self, bin_obj, quantity):
        """Update Digital Twin occupancy via DigitalTwinSyncService."""
        from apps.warehouse.application.services.digital_twin_sync_service import DigitalTwinSyncService
        DigitalTwinSyncService.sync_occupancy(
            bin_id=bin_obj.id,
            is_occupied=True,
            capacity_delta=quantity
        )



class AIRecommendationViewSet(viewsets.GenericViewSet):
    def get_serializer_class(self):
        if self.action == 'predict_demand':
            return DemandForecastSerializer
        elif self.action == 'congestion_risk':
            return CongestionPredictionSerializer
        return RecommendationSerializer

    @action(detail=False, methods=['post'], url_path='predict-demand')
    def predict_demand(self, request):
        """
        POST /api/ai/predict-demand/
        {
            "product_id": "SKU_123" or UUID,
            "days_history": 30 (optional)
        }
        """
        product_id = request.data.get('product_id')
        days_history = request.data.get('days_history', 30)

        if not product_id:
            return Response({"error": "product_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            forecast = AISlottingEngine.forecast_demand(product_id, int(days_history))
            serializer = DemandForecastSerializer(forecast)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='optimize-slotting')
    def optimize_slotting(self, request):
        """
        POST /api/ai/optimize-slotting/
        {
            "product_id": "SKU_123" or UUID,
            "warehouse_id": "..."
        }
        """
        product_id = request.data.get('product_id')
        warehouse_id = request.data.get('warehouse_id')

        if not all([product_id, warehouse_id]):
            return Response({"error": "product_id and warehouse_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            recommendation = AISlottingEngine.optimize_slotting(product_id, warehouse_id)
            serializer = RecommendationSerializer(recommendation)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='congestion-risk')
    def congestion_risk(self, request):
        """
        GET /api/ai/congestion-risk/?warehouse_id=...
        """
        warehouse_id = request.query_params.get('warehouse_id')
        if not warehouse_id:
            return Response({"error": "warehouse_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            predictions = AISlottingEngine.predict_congestion_risk(warehouse_id)
            serializer = CongestionPredictionSerializer(predictions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to predict congestion risk: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='recommendations')
    def recommendations(self, request):
        """
        GET /api/ai/recommendations/
        """
        recs = AllocationRecommendation.objects.all().order_by('-created_at')
        serializer = RecommendationSerializer(recs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='slotting-score')
    def slotting_score(self, request):
        """
        GET /api/ai/slotting-score/?product_id=...&warehouse_id=...
        """
        product_id = request.query_params.get('product_id')
        warehouse_id = request.query_params.get('warehouse_id')
        if not all([product_id, warehouse_id]):
            return Response({"error": "product_id and warehouse_id query parameters are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            scores = AISlottingEngine.calculate_all_slotting_scores(product_id, warehouse_id)
            # Remove Django model instances before sending JSON response
            cleaned_scores = []
            for sc in scores:
                cleaned_scores.append({
                    "bin_code": sc["bin_code"],
                    "zone_name": sc["zone_name"],
                    "score": sc["score"],
                    "proximity_reward": sc["proximity_reward"],
                    "congestion_penalty": sc["congestion_penalty"],
                    "travel_cost": sc["travel_cost"],
                    "affinity_bonus": sc["affinity_bonus"]
                })
            return Response(cleaned_scores, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='hotspot-prevention')
    def hotspot_prevention(self, request):
        """
        GET /api/ai/hotspot-prevention/?warehouse_id=...
        """
        warehouse_id = request.query_params.get('warehouse_id')
        if not warehouse_id:
            return Response({"error": "warehouse_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            res = HotspotPreventionEngine.analyze_hotspots(warehouse_id)
            return Response(res, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed hotspot analysis: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='operational-scores')
    def operational_scores(self, request):
        """
        GET /api/ai/operational-scores/?warehouse_id=...
        """
        warehouse_id = request.query_params.get('warehouse_id')
        if not warehouse_id:
            return Response({"error": "warehouse_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            res = OperationalScoringEngine.calculate_operational_scores(warehouse_id)
            return Response(res, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to compute operational scores: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get', 'post'], url_path='alerts')
    def alerts(self, request):
        """
        GET /api/ai/alerts/
        POST /api/ai/alerts/ (body: {"alert_id": "..."}) - Resolves alert
        """
        if request.method == 'GET':
            alerts = SystemAlert.objects.all().order_by('-created_at')
            serializer = SystemAlertSerializer(alerts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'POST':
            alert_id = request.data.get('alert_id')
            if not alert_id:
                return Response({"error": "alert_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                alert = SystemAlert.objects.get(id=alert_id)
                alert.is_resolved = True
                alert.resolved_at = timezone.now()
                alert.save()
                return Response({"success": True, "message": "Alert marked resolved."}, status=status.HTTP_200_OK)
            except SystemAlert.DoesNotExist:
                return Response({"error": "Alert not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='feedback')
    def feedback(self, request):
        """
        POST /api/ai/feedback/
        {
            "signal_type": "PICK_DURATION",
            "payload": {
                "duration": 55.2,
                "benchmark": 40.0,
                "decision_id": "...",
                "history_id": "..."
            }
        }
        """
        signal_type = request.data.get('signal_type')
        payload = request.data.get('payload')
        if not all([signal_type, payload]):
            return Response({"error": "signal_type and payload are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            res = AIFeedbackLoop.process_feedback_signal(signal_type, payload)
            return Response(res, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed feedback ingestion: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


