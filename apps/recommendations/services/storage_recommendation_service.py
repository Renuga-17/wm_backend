import logging
from django.db import transaction
from apps.inventory.infrastructure.persistence.models import Product
from ..models.product_classification import ProductClassification
from ..models.storage_recommendation import StorageRecommendation
from apps.warehouse.models import ZoneGroup, Zone
from .recommendation_orchestrator import RecommendationOrchestrator
from .zone_selection_service import ZoneSelectionService

logger = logging.getLogger(__name__)

class StorageRecommendationService:
    """Orchestrates validation, runs orchestrator to get recommendations, and persists the decision.
    """

    def __init__(self):
        self.orchestrator = RecommendationOrchestrator()
        self.zone_selector = ZoneSelectionService()

    def generate_recommendation(self, product_id) -> StorageRecommendation:
        logger.info("StorageRecommendationService: Received request for product_id: %s", product_id)
        
        # Validation 1: Product exists
        try:
            product = Product.objects.get(id=product_id)
        except (Product.DoesNotExist, ValueError):
            logger.error("StorageRecommendationService: Product not found with ID %s", product_id)
            raise ValueError(f"Product not found for ID: {product_id}")
            
        # Validation 2: ProductClassification exists
        try:
            classification = ProductClassification.objects.get(product=product)
        except ProductClassification.DoesNotExist:
            logger.error("StorageRecommendationService: ProductClassification not found for product %s", product.sku)
            raise ValueError(f"Product classification does not exist for product: {product.sku}")
            
        # Run orchestrator
        rec_data = self.orchestrator.get_recommendation(product)
        zone_group = rec_data['zone_group']
        zone = rec_data['zone']
        
        # Validation 3: ZoneGroup exists
        if not ZoneGroup.objects.filter(id=zone_group.id).exists():
            logger.error("StorageRecommendationService: Selected ZoneGroup %s does not exist in database", zone_group.code)
            raise ValueError(f"Selected ZoneGroup {zone_group.code} does not exist in database")
            
        # Validation 4: Zone exists
        if not Zone.objects.filter(id=zone.id).exists():
            logger.error("StorageRecommendationService: Selected Zone %s does not exist in database", zone.zone_name)
            raise ValueError(f"Selected Zone {zone.zone_name} does not exist in database")
            
        # Validation 5: Available capacity exists (checked during zone ranking)
        metrics = self.zone_selector.calculate_zone_capacity_metrics(zone)
        if metrics['total_capacity'] <= 0.0:
            logger.error("StorageRecommendationService: Selected Zone %s has no configured capacity bins", zone.zone_name)
            raise ValueError(f"Selected Zone {zone.zone_name} has no capacity bins defined")
            
        # Persist recommendation
        with transaction.atomic():
            recommendation = StorageRecommendation.objects.create(
                product=product,
                zone_group=zone_group,
                zone=zone,
                recommendation_reason=rec_data['recommendation_reason'],
                recommendation_score=rec_data['recommendation_score'],
                recommendation_source=rec_data['recommendation_source'],
                recommendation_version=rec_data['recommendation_version']
            )
            
        logger.info(
            "StorageRecommendationService: Persisted recommendation %s (score=%.4f) for product %s",
            recommendation.id, recommendation.recommendation_score, product.sku
        )
        return recommendation
