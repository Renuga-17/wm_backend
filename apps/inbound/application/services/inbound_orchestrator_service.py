import logging
import traceback
from django.db import transaction
from django.utils import timezone
from apps.inbound.infrastructure.persistence.models import OCRDocument, InboundShipment
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, ProductDimension
from apps.recommendations.models.product_classification import ProductClassification
from apps.recommendations.models.recommendation_rule import RecommendationRule
from apps.recommendations.services.storage_recommendation_service import StorageRecommendationService
from apps.recommendations.services.bin_allocation_service import BinAllocationService
from apps.recommendations.services.three_d_optimization_service import ThreeDOptimizationService
from apps.warehouse.application.services.route_optimizer import RouteOptimizer
from apps.warehouse.infrastructure.persistence.models import NavigationNode
from apps.inbound.application.services.rag_service import send_to_rag

logger = logging.getLogger(__name__)


class InboundOrchestratorService:
    def orchestrate_inbound(self, ocr_document: OCRDocument, custom_payload: dict = None) -> InboundShipment:
        """
        Orchestrates the downstream WMS ingestion pipeline atomically.
        Accepts custom_payload when an operator manually approves and edits
        the data from a low-confidence OCR document.
        """
        logger.info("InboundOrchestratorService: Starting ingestion for OCR Document %s", ocr_document.id)
        
        # Use provided custom_payload or fall back to document's extracted JSON
        payload = custom_payload if custom_payload is not None else ocr_document.extracted_json
        if not payload:
            payload = {}
        
        extracted_data = payload.get('extracted_data', {})

        products_list = extracted_data.get('products', [])
        if not products_list:
            products_list = payload.get('storage_payloads', {}).get('product_payload', [])

        rag_metadata = {
            "ocr_document_id": str(ocr_document.id),
            "document_type": "OCRDocument",
            "text": ocr_document.raw_text,
            "warehouse_id": "WH001",
            "sku": None,
            "product_id": None,
            "category": None,
            "zone": None,
            "rack": None,
            "shelf": None,
            "bin": None,
        }

        try:
            with transaction.atomic():
                # Step A: Parse and Create InboundShipment
                doc_info = extracted_data.get('document_info', {})
                party_info = extracted_data.get('party_info', {})
                shipment_info = extracted_data.get('shipment_info', {})

                shipment_code = (
                    doc_info.get('invoice_number') 
                    or doc_info.get('document_number') 
                    or doc_info.get('delivery_number') 
                    or f"INB-{ocr_document.document_hash[:8]}"
                )
                supplier_name = party_info.get('supplier_name') or "Unknown Supplier"
                expected_arrival = shipment_info.get('delivery_date') or timezone.now()

                # Ensure unique shipment code
                orig_code = shipment_code
                counter = 1
                while InboundShipment.objects.filter(shipment_code=shipment_code).exists():
                    shipment_code = f"{orig_code}-{counter}"
                    counter += 1

                shipment = InboundShipment.objects.create(
                    shipment_code=shipment_code,
                    supplier_name=supplier_name,
                    expected_arrival=expected_arrival,
                    status='RECEIVED'
                )

                # Step B: Loop products & create
                for prod_item in products_list:
                    sku = prod_item.get('sku')
                    if not sku:
                        continue

                    category_name = prod_item.get('category') or 'General'
                    category, _ = ProductCategory.objects.get_or_create(category_name=category_name)

                    # Get weight
                    weight_data = prod_item.get('weight') or {}
                    if isinstance(weight_data, dict):
                        weight_val = weight_data.get('value') or 0.0
                    else:
                        weight_val = float(weight_data or 0.0)

                    # Update or Create Product
                    product_obj, _ = Product.objects.update_or_create(
                        sku=sku,
                        defaults={
                            "product_name": prod_item.get('product_name') or sku,
                            "category": category,
                            "weight": weight_val,
                            "is_fragile": prod_item.get('is_fragile', False),
                            "is_hazardous": prod_item.get('is_hazardous', False)
                        }
                    )

                    # Create ProductDimension
                    dim_data = prod_item.get('dimensions') or {}
                    length = dim_data.get('length') or 0.0
                    width = dim_data.get('width') or 0.0
                    height = dim_data.get('height') or 0.0

                    ProductDimension.objects.update_or_create(
                        product=product_obj,
                        defaults={
                            "length": length,
                            "width": width,
                            "height": height,
                            "box_length": length * 1.05,
                            "box_width": width * 1.05,
                            "box_height": height * 1.05
                        }
                    )

                    # Create ProductClassification
                    movement_type = 'FAST'
                    storage_type = 'GENERAL'
                    if product_obj.is_fragile:
                        movement_type = 'FRAGILE'
                    elif product_obj.is_hazardous:
                        movement_type = 'HAZARDOUS'

                    ProductClassification.objects.update_or_create(
                        product=product_obj,
                        defaults={
                            "movement_type": movement_type,
                            "storage_type": storage_type
                        }
                    )

                    # Ensure recommendation rule exists
                    RecommendationRule.objects.get_or_create(
                        movement_type=movement_type,
                        storage_type=storage_type,
                        defaults={
                            'zone_group_type': 'GENERAL_STORAGE',
                            'priority': 10,
                            'description': 'Auto-generated rule during orchestration'
                        }
                    )

                    # Step C: Storage Recommendation
                    rec_svc = StorageRecommendationService()
                    rec_svc.generate_recommendation(product_obj.id)

                    # Step D: Bin Allocation
                    alloc_svc = BinAllocationService()
                    allocation = alloc_svc.generate_bin_allocation(product_obj.id)

                    # Step E: 3D Placement
                    opt_3d_svc = ThreeDOptimizationService()
                    opt_3d_svc.evaluate_placement(allocation)

                    # Step F: Route Generation (3D path finding)
                    warehouse = allocation.bin.shelf.rack.zone.warehouse
                    start_node = NavigationNode.objects.filter(warehouse=warehouse, node_type__iexact='DOCK').first()
                    if not start_node:
                        start_node = NavigationNode.objects.filter(warehouse=warehouse).first()

                    if start_node:
                        try:
                            RouteOptimizer.compute_route(
                                warehouse_id=warehouse.id,
                                start_location=start_node.node_name,
                                target_location=allocation.bin.bin_code
                            )
                        except Exception as route_err:
                            logger.warning("InboundOrchestratorService: Route computation failed: %s", route_err)

                    # Update metadata for RAG (first product info as representative)
                    if not rag_metadata["sku"]:
                        rag_metadata.update({
                            "sku": sku,
                            "product_id": str(product_obj.id),
                            "category": category_name,
                            "warehouse_id": str(allocation.zone.warehouse_id),
                            "zone": allocation.zone.zone_name,
                            "rack": allocation.rack.rack_code,
                            "shelf": str(allocation.shelf.shelf_number),
                            "bin": allocation.bin.bin_code,
                        })

                # Mark document as COMPLETED
                ocr_document.processing_status = OCRDocument.ProcessingStatus.COMPLETED
                ocr_document.error_message = None
                ocr_document.save()

            # The database transaction has successfully committed!
            logger.info("InboundOrchestratorService: DB ingestion successful.")

        except Exception as e:
            # Transaction rollbacks automatically. Update document status to FAILED.
            logger.exception("InboundOrchestratorService: Ingestion failed, rolling back. Error: %s", e)
            
            # Update OCRDocument status to FAILED in a separate query outside transaction context
            OCRDocument.objects.filter(id=ocr_document.id).update(
                processing_status=OCRDocument.ProcessingStatus.FAILED,
                error_message=f"Pipeline error: {str(e)}\n{traceback.format_exc()}"
            )
            raise e

        # Step G: Send to RAG ingestion asynchronously (non-blocking, outside database transaction)
        try:
            from apps.inbound.tasks import sync_rag_task
            sync_rag_task.delay(str(ocr_document.id))
            logger.info("InboundOrchestratorService: RAG sync task queued successfully.")
        except Exception as rag_err:
            logger.warning("InboundOrchestratorService: Queueing RAG ingestion failed: %s", rag_err)

        return shipment
