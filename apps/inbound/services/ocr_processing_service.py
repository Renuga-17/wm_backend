import logging
import traceback
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from apps.inbound.infrastructure.persistence.models import OCRDocument, InboundShipment
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, ProductDimension
from apps.recommendations.models.product_classification import ProductClassification
from apps.recommendations.models.recommendation_rule import RecommendationRule
from apps.recommendations.services.storage_recommendation_service import StorageRecommendationService
from apps.recommendations.services.bin_allocation_service import BinAllocationService
from apps.recommendations.services.three_d_optimization_service import ThreeDOptimizationService
from apps.warehouse.application.services.route_optimizer import RouteOptimizer
from apps.warehouse.infrastructure.persistence.models import NavigationNode
from .ocr_client import OCRClient, OCRClientException

logger = logging.getLogger(__name__)


class OCRProcessingService:
    def __init__(self):
        self.client = OCRClient()

    def process_document(self, document_id) -> None:
        """Processes the OCRDocument: calls the OCR service, stores the results,
        and triggers the downstream WMS ingestion pipeline (Inbound, Products, Recommendations,
        Allocations, 3D Placements, and Routes).
        """
        logger.info("OCRProcessingService: Starting processing for document ID: %s", document_id)
        try:
            ocr_doc = OCRDocument.objects.get(id=document_id)
        except OCRDocument.DoesNotExist:
            logger.error("OCRProcessingService: Document ID %s not found.", document_id)
            return

        # 1. Update status to PROCESSING
        ocr_doc.processing_status = OCRDocument.ProcessingStatus.PROCESSING
        ocr_doc.save()

        # 2. Call OCR microservice
        try:
            # Read file bytes
            file_full_path = ocr_doc.file_path
            # Since files are saved via default_storage, we open the file
            from django.core.files.storage import default_storage
            with default_storage.open(file_full_path, 'rb') as f:
                file_bytes = f.read()

            ocr_res = self.client.extract_document(
                file_bytes=file_bytes,
                file_name=ocr_doc.file_name,
                content_type='application/pdf' if ocr_doc.file_name.lower().endswith('.pdf') else 'image/png'
            )
        except Exception as e:
            logger.error("OCRProcessingService: OCR client failed: %s", e)
            ocr_doc.processing_status = OCRDocument.ProcessingStatus.FAILED
            ocr_doc.error_message = str(e)
            ocr_doc.save()
            return

        # 3. Parse responses
        raw_text = ocr_res.get('raw_text', '')
        extracted_data = ocr_res.get('extracted_data', {})
        confidence_score = ocr_res.get('confidence_score', 0.0)
        doc_type = ocr_res.get('document_type') or ocr_doc.document_type or 'invoice'

        # Store raw text and extracted JSON on the document
        ocr_doc.raw_text = raw_text
        ocr_doc.extracted_json = ocr_res
        ocr_doc.confidence_score = confidence_score
        ocr_doc.document_type = doc_type

        # 4. Review queue logic (Phase 6): check confidence score
        if confidence_score < 0.85:
            ocr_doc.processing_status = OCRDocument.ProcessingStatus.REVIEW_REQUIRED
            ocr_doc.save()
            logger.warning("OCRProcessingService: Confidence score %.2f is below threshold. Review required.", confidence_score)
            return

        # 5. Domain WMS objects creation (Inbound Document, Product/Dimensions, Recommendations, Routing)
        try:
            with transaction.atomic():
                # Step A: Create Inbound Document (InboundShipment)
                doc_info = extracted_data.get('document_info', {})
                party_info = extracted_data.get('party_info', {})
                shipment_info = extracted_data.get('shipment_info', {})

                shipment_code = doc_info.get('invoice_number') or doc_info.get('document_number') or doc_info.get('delivery_number') or f"INB-{ocr_doc.document_hash[:8]}"
                supplier_name = party_info.get('supplier_name') or "Unknown Supplier"
                expected_arrival = shipment_info.get('delivery_date') or timezone.now()

                # Ensure unique shipment_code
                orig_code = shipment_code
                counter = 1
                while InboundShipment.objects.filter(shipment_code=shipment_code).exists():
                    shipment_code = f"{orig_code}-{counter}"
                    counter += 1

                InboundShipment.objects.create(
                    shipment_code=shipment_code,
                    supplier_name=supplier_name,
                    expected_arrival=expected_arrival,
                    status='RECEIVED'
                )

                # Step B: Loop products & create
                products_list = extracted_data.get('products', [])
                if not products_list:
                    # fallback if products list is not in extracted_data
                    products_list = ocr_res.get('storage_payloads', {}).get('product_payload', [])

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

                    # Create ProductClassification to satisfy recommendations validation
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
                            'description': 'Auto-generated rule during OCR integration'
                        }
                    )

                    # Step C: Storage Recommendation
                    rec_svc = StorageRecommendationService()
                    recommendation = rec_svc.generate_recommendation(product_obj.id)

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
                            logger.warning("OCRProcessingService: Route computation failed: %s", route_err)

            ocr_doc.processing_status = OCRDocument.ProcessingStatus.COMPLETED
            ocr_doc.error_message = None
            ocr_doc.save()
            logger.info("OCRProcessingService: Processing completed successfully for document %s", document_id)

        except Exception as pipe_err:
            logger.exception("OCRProcessingService: Ingestion pipeline failed: %s", pipe_err)
            ocr_doc.processing_status = OCRDocument.ProcessingStatus.FAILED
            ocr_doc.error_message = f"Pipeline error: {str(pipe_err)}\n{traceback.format_exc()}"
            ocr_doc.save()

        # Step G: Send to RAG ingestion if text is available
        try:
            from apps.inbound.application.services.rag_service import send_to_rag
            send_to_rag(
                ocr_document_id=str(ocr_doc.id),
                document_type="OCRDocument",
                warehouse_id="WH001",
                text=ocr_doc.raw_text,
            )
        except Exception as rag_err:
            logger.warning("OCRProcessingService: RAG ingestion trigger failed: %s", rag_err)
