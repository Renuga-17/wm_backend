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

            # 6. Evaluate 3D placement optimization
            from .three_d_optimization_service import ThreeDOptimizationService
            three_d_service = ThreeDOptimizationService()
            placement_3d = three_d_service.evaluate_placement(allocation)

            # 7. Compute route optimization
            from apps.warehouse.application.services.route_optimizer import RouteOptimizer
            from apps.warehouse.infrastructure.persistence.models import NavigationNode
            
            start_location = "DOCK_A"
            docks = NavigationNode.objects.filter(warehouse=zone.warehouse, node_type__iexact='DOCK')
            dock = docks.first()
            if dock is not None:
                start_location = dock.node_name
                
            try:
                route_data = RouteOptimizer.compute_route(
                    warehouse_id=zone.warehouse.id,
                    start_location=start_location,
                    target_location=bin_obj.bin_code
                )
            except Exception as e:
                logger.warning("Route calculation failed: %s. Using fallback node.", str(e))
                route_data = {
                    "start_location": start_location,
                    "distance": 0.0,
                    "path": []
                }

            # 8. Generate navigation guidance (automatic, deterministic first)
            from .ai_navigation_guidance_service import AINavigationGuidanceService
            nav_service = AINavigationGuidanceService()
            route_data["start_location"] = start_location
            nav_instructions = nav_service.generate_instructions(
                zone=zone,
                rack=bin_obj.shelf.rack,
                shelf=bin_obj.shelf,
                bin_obj=bin_obj,
                route_data=route_data
            )

            # 9. Generate placement guidance (automatic, deterministic first)
            from .ai_placement_guidance_service import AIPlacementGuidanceService
            placement_service = AIPlacementGuidanceService()
            placement_instructions = placement_service.generate_instructions(
                product_dim=product_dimension,
                selected_orientation=allocation.selected_orientation,
                placement_3d=placement_3d,
                bin_obj=bin_obj
            )

            # 10. Cache instructions on the allocation model
            allocation.navigation_instructions = nav_instructions
            allocation.placement_instructions = placement_instructions
            allocation.save()

        logger.info(
            "BinAllocationService: Successfully persisted BinAllocation %s (Score: %.4f, Bin: %s) for product %s with navigation and placement guidance.",
            allocation.id, score, bin_obj.bin_code, product.sku  # type: ignore
        )
        return allocation
