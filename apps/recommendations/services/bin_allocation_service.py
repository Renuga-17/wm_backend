import logging
from django.db import transaction
from apps.inventory.infrastructure.persistence.models import Product, ProductDimension
from ..models.storage_recommendation import StorageRecommendation
from ..models.bin_allocation import BinAllocation
from .allocation_orchestrator import AllocationOrchestrator

logger = logging.getLogger(__name__)

class ProductNotFoundError(ValueError):
    pass

class RecommendationNotFoundError(ValueError):
    pass

class DimensionsNotFoundError(ValueError):
    pass

class AllocationFailedError(ValueError):
    pass

class BinAllocationService:
    def __init__(self):
        self.orchestrator = AllocationOrchestrator()

    def generate_bin_allocation(self, product_id) -> BinAllocation:
        logger.info("BinAllocationService: Received bin allocation request for product_id: %s", product_id)

        # 1. Validate: Product exists
        try:
            product = Product.objects.get(id=product_id)
        except (Product.DoesNotExist, ValueError):
            logger.error("BinAllocationService: Product not found with ID %s", product_id)
            raise ProductNotFoundError("Product not found")

        # 2. Validate: ProductDimension exists
        try:
            # Get first dimension
            product_dimension = ProductDimension.objects.filter(product=product).first()
            if not product_dimension:
                raise ProductDimension.DoesNotExist()
        except ProductDimension.DoesNotExist:
            logger.error("BinAllocationService: Product dimensions not found for product %s", product.sku)
            raise DimensionsNotFoundError("Product dimensions not found")

        # 3. Validate: Latest StorageRecommendation exists
        latest_rec = StorageRecommendation.objects.filter(product=product).order_by('-created_at', '-id').first()
        if not latest_rec:
            logger.error("BinAllocationService: Storage recommendation not found for product %s", product.sku)
            raise RecommendationNotFoundError("Storage recommendation not found")

        zone_group = latest_rec.zone_group
        zone = latest_rec.zone

        # 4. Orchestrate allocation selection
        bin_obj, orientation, score, reason = self.orchestrator.find_allocation(zone, product, product_dimension)
        if not bin_obj:
            logger.error("BinAllocationService: Allocation failed for product %s in zone %s: %s", product.sku, zone.zone_name, reason)
            raise AllocationFailedError(reason)

        # 5. Persist the allocation
        with transaction.atomic():
            allocation = BinAllocation.objects.create(
                product=product,
                zone_group=zone_group,
                zone=zone,
                rack=bin_obj.shelf.rack,
                shelf=bin_obj.shelf,
                bin=bin_obj,
                allocation_score=score,
                allocation_reason=reason,
                allocation_source=BinAllocation.AllocationSource.RULE_ENGINE,
                allocation_version='v1',
                selected_orientation=orientation
            )

        logger.info(
            "BinAllocationService: Successfully persisted BinAllocation %s (Score: %.4f, Bin: %s) for product %s",
            allocation.id, score, bin_obj.bin_code, product.sku
        )
        return allocation
