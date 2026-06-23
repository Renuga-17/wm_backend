import pytest
from decimal import Decimal
from django.utils import timezone
from apps.inbound.infrastructure.persistence.models import OCRDocument, InboundShipment, InboundShipmentLine, PutawayTask
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, Inventory
from apps.inventory.infrastructure.persistence.movement_models import StockMovement
from apps.warehouse.infrastructure.persistence.models import Warehouse, Zone, ZoneGroup, Rack, Shelf, Bin, WarehouseLayout
from apps.recommendations.models.bin_allocation import BinAllocation
from apps.inbound.application.services.inbound_orchestrator_service import InboundOrchestratorService


@pytest.fixture
def db_setup(db):
    # Create structure
    warehouse = Warehouse.objects.create(name="Central Warehouse", location="Dock A")
    layout = WarehouseLayout.objects.create(
        warehouse=warehouse,
        layout_name="Default Layout",
        cad_file_url="/media/layouts/test.dxf",
        width=100.0, height=100.0, depth=10.0
    )
    zone_group = ZoneGroup.objects.create(
        warehouse=warehouse,
        code="GENERAL_STORAGE",
        name="General Zone Group",
        zone_group_type="GENERAL_STORAGE"
    )
    zone = Zone.objects.create(
        warehouse=warehouse,
        zone_group=zone_group,
        zone_name="Zone A",
        zone_type="DRY",
        x=0.0, y=0.0, z=0.0, width=50.0, height=50.0, depth=5.0
    )
    rack = Rack.objects.create(
        zone=zone,
        rack_code="RACK-A1",
        max_weight=1000.0,
        x=10.0, y=10.0, z=0.0, width=10.0, height=2.0, depth=3.0,
        rotation_angle=0.0
    )
    shelf = Shelf.objects.create(
        rack=rack,
        shelf_number=1,
        max_weight=500.0,
        height_from_ground=0.5
    )
    bin_obj = Bin.objects.create(
        shelf=shelf,
        bin_code="RACK-A1-01-L1-B01",
        max_capacity=Decimal('100.00'),
        current_capacity=Decimal('0.00'),
        length=Decimal('50.00'),
        width=Decimal('50.00'),
        height=Decimal('50.00'),
        is_occupied=False
    )
    return {
        "warehouse": warehouse,
        "zone": zone,
        "bin": bin_obj
    }


@pytest.mark.django_db
def test_complete_inbound_putaway_lifecycle(db_setup, monkeypatch):
    # Mock route optimizer to bypass external service calls or complex queries
    from apps.warehouse.application.services.route_optimizer import RouteOptimizer
    monkeypatch.setattr(RouteOptimizer, "compute_route", lambda **kwargs: {"distance": 10.0, "path": []})

    # 1. OCR verification approval setup
    extracted_json = {
        "extracted_data": {
            "document_info": {
                "invoice_number": "INV-2026-999"
            },
            "party_info": {
                "supplier_name": "Acme Industrial Suppliers"
            },
            "shipment_info": {
                "delivery_date": "2026-06-25T12:00:00Z"
            },
            "products": [
                {
                    "sku": "SKU-TEST-999",
                    "product_name": "Premium Industrial Gears",
                    "category": "Machinery Parts",
                    "quantity": 75,
                    "weight": 12.5,
                    "dimensions": {
                        "length": 15.0,
                        "width": 10.0,
                        "height": 8.0
                    },
                    "is_fragile": False,
                    "is_hazardous": False
                }
            ]
        }
    }

    ocr_doc = OCRDocument.objects.create(
        file_name="invoice_999.pdf",
        file_path="ocr_documents/invoice_999.pdf",
        document_type="invoice",
        document_hash="999f8d7c6b5a",
        extracted_json=extracted_json,
        processing_status=OCRDocument.ProcessingStatus.REVIEW_REQUIRED
    )

    # Trigger Inbound ingestion
    orchestrator = InboundOrchestratorService()
    shipment = orchestrator.orchestrate_inbound(ocr_doc)

    # Verification: InboundShipment header exists and is correct
    assert shipment is not None
    assert shipment.shipment_code == "INV-2026-999"
    assert shipment.supplier_name == "Acme Industrial Suppliers"
    assert shipment.ocr_document == ocr_doc

    # Verification: InboundShipmentLine exists and is correct
    lines = list(shipment.line_items.all())
    assert len(lines) == 1
    line = lines[0]
    assert line.sku == "SKU-TEST-999"
    assert line.product_name == "Premium Industrial Gears"
    assert line.quantity == 75
    assert line.weight == Decimal('12.50')
    assert line.dimensions == "15.0x10.0x8.0 cm"
    assert line.recommendation_status == "RECOMMENDED"

    # Verification: Product is updated or created without duplicates
    product = Product.objects.get(sku="SKU-TEST-999")
    assert product.product_name == "Premium Industrial Gears"

    # Verification: BinAllocation is persisted and linked
    allocations = list(BinAllocation.objects.filter(inbound_line=line))
    assert len(allocations) == 1
    allocation = allocations[0]
    assert allocation.product == product
    assert allocation.inbound_shipment == shipment
    assert allocation.storage_status == BinAllocation.StorageStatus.ALLOCATED

    # 2. Putaway Task Dispatch
    # Operator confirms / manager dispatches
    operator_username = "operator_alex"
    task = PutawayTask.objects.create(
        operator=operator_username,
        inbound_shipment=shipment,
        inbound_line=line,
        product=product,
        quantity=line.quantity,
        destination_bin=db_setup["bin"],
        status=PutawayTask.PutawayStatus.ASSIGNED
    )
    
    # Assert dispatch is stored
    assert task.status == PutawayTask.PutawayStatus.ASSIGNED
    assert task.operator == "operator_alex"
    assert task.destination_bin == db_setup["bin"]

    # 3. Simulate Operator flow: START
    task.status = PutawayTask.PutawayStatus.IN_PROGRESS
    task.save()
    assert PutawayTask.objects.get(id=task.id).status == PutawayTask.PutawayStatus.IN_PROGRESS

    # 4. Simulate Operator flow: REACHED_BIN
    task.status = PutawayTask.PutawayStatus.REACHED_BIN
    task.save()
    assert PutawayTask.objects.get(id=task.id).status == PutawayTask.PutawayStatus.REACHED_BIN

    # 5. Simulate Operator flow: COMPLETE
    from rest_framework.test import APIClient
    from apps.identity.infrastructure.persistence.models import User

    user = User.objects.create_user(username='testadmin', password='pass1234')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(f'/api/inbound/putaway/{task.id}/complete/', {"operator": operator_username}, format='json')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data if hasattr(response, 'data') else response.content}"
    assert response.data["status"] == "COMPLETED"

    # Reload database objects to verify state survival
    task.refresh_from_db()
    line.refresh_from_db()
    shipment.refresh_from_db()
    bin_obj = db_setup["bin"]
    bin_obj.refresh_from_db()

    # Verification: Operator task completion matches
    assert task.status == PutawayTask.PutawayStatus.COMPLETED
    assert task.completed_at is not None

    # Verification: Inbound line & shipment status updated to STORED
    assert line.recommendation_status == "STORED"
    assert shipment.status == "STORED"

    # Verification: Inventory is updated correctly
    inventory_record = Inventory.objects.get(product=product)
    assert inventory_record.total_quantity == 75

    # Verification: StockMovement logged
    movements = list(StockMovement.objects.filter(product=product, movement_type="PUTAWAY_COMPLETED"))
    assert len(movements) == 1
    mv = movements[0]
    assert mv.quantity == 75
    assert mv.to_bin == bin_obj
    assert mv.operator == operator_username

    # Verification: Bin capacity & occupied state updated
    assert bin_obj.current_capacity == Decimal('75.00')
    assert bin_obj.is_occupied is True

    # Verification: BinAllocation status updated to STORED
    allocation.refresh_from_db()
    assert allocation.storage_status == BinAllocation.StorageStatus.STORED
    assert allocation.stored_at is not None
    assert allocation.operator == operator_username
