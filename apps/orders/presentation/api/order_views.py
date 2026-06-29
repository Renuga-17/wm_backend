from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError

from apps.orders.infrastructure.persistence.models import OutboundShipment
from apps.inventory.infrastructure.persistence.models import Product, StorageAllocation, Inventory, StockMovement
from apps.warehouse.infrastructure.persistence.models import Bin, StorageLocationNodeMap, NavigationNode
from apps.identity.infrastructure.persistence.models import AuditLog
from apps.warehouse.application.services.digital_twin_sync_service import DigitalTwinSyncService
from apps.warehouse.application.services.pathfinding import PathfindingService

from .serializers import (
    OrderSerializer,
    GeneratePickListSerializer,
    AssignPickerSerializer,
    OptimizeRouteSerializer,
    PackItemsSerializer,
    OutboundOperationSerializer
)

def get_shipment(shipment_id):
    try:
        return OutboundShipment.objects.get(id=shipment_id)
    except (OutboundShipment.DoesNotExist, ValueError, ValidationError):
        return OutboundShipment.objects.filter(shipment_code=shipment_id).first()

def get_product(product_id):
    try:
        return Product.objects.get(id=product_id)
    except (Product.DoesNotExist, ValueError, ValidationError):
        return Product.objects.filter(sku=product_id).first()

class OrderViewSet(viewsets.ModelViewSet):
    queryset = OutboundShipment.objects.all()
    serializer_class = OrderSerializer

    @action(detail=False, methods=['post'], url_path='generate-picklist')
    def generate_picklist(self, request):
        """
        POST /api/orders/generate-picklist/
        Generates a picklist based on stock availability and maps product allocations.
        """
        serializer = GeneratePickListSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        shipment = get_shipment(serializer.validated_data['shipment_id'])
        if not shipment:
            return Response({"error": "Shipment not found"}, status=status.HTTP_404_NOT_FOUND)

        if not shipment.items:
            return Response({"error": "Shipment has no items to pick"}, status=status.HTTP_400_BAD_REQUEST)

        allocated_picks = []

        # Validate stock and select bins (FIFO based on allocated_at)
        for item in shipment.items:
            product = get_product(item['product_id'])
            if not product:
                return Response({"error": f"Product {item['product_id']} not found"}, status=status.HTTP_400_BAD_REQUEST)

            qty_needed = item['quantity']
            allocations = StorageAllocation.objects.filter(product=product).order_by('allocated_at')
            total_avail = sum(a.quantity for a in allocations)

            if total_avail < qty_needed:
                return Response({
                    "error": f"Insufficient stock for product {product.sku}. Available: {total_avail}, Required: {qty_needed}"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Perform allocation mapping
            for alloc in allocations:
                if qty_needed <= 0:
                    break
                pick_qty = min(alloc.quantity, qty_needed)
                allocated_picks.append({
                    "product_id": str(product.id),
                    "sku": product.sku,
                    "product_name": product.product_name,
                    "bin_id": str(alloc.bin.id),
                    "bin_code": alloc.bin.bin_code,
                    "quantity_to_pick": pick_qty,
                    "picked_quantity": 0
                })
                qty_needed -= pick_qty

        # Commit picklist configuration to shipment
        shipment.picklist = {
            "status": "PENDING",
            "picker": None,
            "items": allocated_picks,
            "route": None
        }
        shipment.status = "PENDING"
        shipment.save()

        return Response({
            "success": True,
            "picklist_id": str(shipment.id),
            "status": shipment.picklist["status"],
            "items": shipment.picklist["items"]
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='assign-picker')
    def assign_picker(self, request):
        """
        POST /api/orders/assign-picker/
        Assigns a picker operator to the picklist and logs the action.
        """
        serializer = AssignPickerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        shipment = get_shipment(serializer.validated_data['picklist_id'])
        if not shipment:
            return Response({"error": "Shipment/Picklist not found"}, status=status.HTTP_404_NOT_FOUND)

        if not shipment.picklist:
            return Response({"error": "Picklist not generated yet for this shipment"}, status=status.HTTP_400_BAD_REQUEST)

        operator = serializer.validated_data['operator']
        shipment.picklist["picker"] = operator
        shipment.picklist["status"] = "ASSIGNED"
        shipment.status = "ASSIGNED"
        shipment.save()

        AuditLog.objects.create(
            user=request.user,
            action_type='PICKER_ASSIGNMENT',
            table_name='outbound_shipments',
            record_id=shipment.id
        )

        return Response({
            "success": True,
            "picklist_id": str(shipment.id),
            "picker": operator,
            "status": "ASSIGNED"
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='optimize-route')
    def optimize_route(self, request):
        """
        POST /api/orders/optimize-route/
        Uses PathfindingService to optimize picking sequence from start node.
        """
        serializer = OptimizeRouteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        shipment = get_shipment(serializer.validated_data['picklist_id'])
        if not shipment:
            return Response({"error": "Shipment/Picklist not found"}, status=status.HTTP_404_NOT_FOUND)

        if not shipment.picklist or not shipment.picklist.get("items"):
            return Response({"error": "Picklist is empty or not generated"}, status=status.HTTP_400_BAD_REQUEST)

        target_nodes = []
        seen_node_ids = set()

        for item in shipment.picklist["items"]:
            try:
                bin_obj = Bin.objects.get(id=item["bin_id"])
            except Bin.DoesNotExist:
                return Response({"error": f"Bin {item['bin_id']} not found"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                node_map = StorageLocationNodeMap.objects.get(bin=bin_obj)
                node = node_map.navigation_node
            except StorageLocationNodeMap.DoesNotExist:
                # Resolve dynamically using pathfinding engine
                warehouse_id = bin_obj.shelf.rack.zone.warehouse_id
                node = PathfindingService.resolve_location_to_node(warehouse_id, bin_obj.bin_code)

            if str(node.id) not in seen_node_ids:
                target_nodes.append(node)
                seen_node_ids.add(str(node.id))

        if not target_nodes:
            return Response({"error": "No routable navigation nodes mapped for picking bins"}, status=status.HTTP_400_BAD_REQUEST)

        # Resolve starting location
        start_node_id = serializer.validated_data.get('start_node_id')
        warehouse_id = target_nodes[0].warehouse_id

        if start_node_id:
            try:
                start_node = NavigationNode.objects.get(id=start_node_id)
            except (NavigationNode.DoesNotExist, ValueError, ValidationError):
                start_node = NavigationNode.objects.filter(node_name=start_node_id, warehouse_id=warehouse_id).first()
                if not start_node:
                    start_node = PathfindingService.resolve_location_to_node(warehouse_id, start_node_id)
        else:
            start_node = target_nodes[0]

        try:
            distance, path_nodes = PathfindingService.nearest_neighbor_tsp(warehouse_id, start_node, target_nodes)
        except Exception as err:
            return Response({"error": f"Route optimization engine failure: {str(err)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Sort the picking list according to the optimized TSP sequence
        node_order = {str(node.id): idx for idx, node in enumerate(path_nodes)}

        def get_picking_index(item):
            try:
                b = Bin.objects.get(id=item["bin_id"])
                nm = StorageLocationNodeMap.objects.get(bin=b)
                return node_order.get(str(nm.navigation_node_id), 9999)
            except Exception:
                return 9999

        shipment.picklist["items"].sort(key=get_picking_index)
        shipment.picklist["route"] = {
            "distance": distance,
            "node_path": [str(node.id) for node in path_nodes]
        }
        shipment.save()

        return Response({
            "success": True,
            "distance": distance,
            "path": [
                {
                    "node_id": str(n.id),
                    "node_name": n.node_name,
                    "x": float(n.x),
                    "y": float(n.y),
                    "z": float(n.z)
                }
                for n in path_nodes
            ],
            "picking_sequence": shipment.picklist["items"]
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='pack')
    def pack(self, request):
        """
        POST /api/orders/pack/
        Verifies packing completion and prevents shortages.
        """
        serializer = PackItemsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        shipment = get_shipment(serializer.validated_data['picklist_id'])
        if not shipment:
            return Response({"error": "Shipment/Picklist not found"}, status=status.HTTP_404_NOT_FOUND)

        if not shipment.picklist:
            return Response({"error": "Picklist not generated yet"}, status=status.HTTP_400_BAD_REQUEST)

        packed_qtys = {}
        for p in serializer.validated_data['packed_items']:
            packed_qtys[p['product_id']] = packed_qtys.get(p['product_id'], 0) + p['quantity']

        # Validate that everything in picklist has been packed accurately (prevent shortages)
        for item in shipment.picklist["items"]:
            prod_id = item["product_id"]
            sku = item["sku"]
            qty_to_pick = item["quantity_to_pick"]
            packed_qty = packed_qtys.get(prod_id, 0)

            # Sum total expected quantity to pick for this product in picklist
            total_expected = sum(i["quantity_to_pick"] for i in shipment.picklist["items"] if i["product_id"] == prod_id)
            total_packed = packed_qtys.get(prod_id, 0)

            if total_packed < total_expected:
                return Response({
                    "error": f"Packing shortage for product {sku}. Expected: {total_expected}, Packed: {total_packed}"
                }, status=status.HTTP_400_BAD_REQUEST)

        # Mark as picked and packed
        for item in shipment.picklist["items"]:
            item["picked_quantity"] = item["quantity_to_pick"]

        for item in shipment.items:
            item["picked_quantity"] = item["quantity"]
            item["packed_quantity"] = item["quantity"]

        shipment.picklist["status"] = "PACKED"
        shipment.status = "PACKED"
        shipment.save()

        return Response({
            "success": True,
            "picklist_id": str(shipment.id),
            "status": "PACKED",
            "message": "Packing validated successfully. All quantities verified."
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='dispatch')
    def dispatch_shipment(self, request):
        """
        POST /api/orders/dispatch/
        Executes dispatch transaction: updates inventory allocations and Digital Twin occupancy.
        """
        serializer = OutboundOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        shipment = get_shipment(serializer.validated_data['picklist_id'])
        if not shipment:
            return Response({"error": "Shipment/Picklist not found"}, status=status.HTTP_404_NOT_FOUND)

        if not shipment.picklist:
            return Response({"error": "Picklist not generated yet"}, status=status.HTTP_400_BAD_REQUEST)

        if shipment.picklist["status"] != "PACKED":
            return Response({"error": "Shipment status must be PACKED to dispatch"}, status=status.HTTP_400_BAD_REQUEST)

        # Perform atomic deductions and updates
        with transaction.atomic():
            for item in shipment.picklist["items"]:
                product = get_product(item["product_id"])
                bin_obj = Bin.objects.get(id=item["bin_id"])
                qty_deduct = item["quantity_to_pick"]

                allocations = StorageAllocation.objects.filter(product=product, bin=bin_obj)
                total_alloc = sum(a.quantity for a in allocations)

                # Ensure dispatch cannot produce negative allocations/inventory
                if total_alloc < qty_deduct:
                    raise ValidationError(f"Cannot dispatch. Allocation in bin {bin_obj.bin_code} is insufficient.")

                remaining = qty_deduct
                for alloc in allocations.order_by('allocated_at'):
                    if remaining <= 0:
                        break
                    if alloc.quantity > remaining:
                        alloc.quantity -= remaining
                        alloc.save()
                        remaining = 0
                    else:
                        remaining -= alloc.quantity
                        alloc.delete()

                # Sync global inventory
                inventory_record, _ = Inventory.objects.get_or_create(
                    product=product,
                    defaults={'total_quantity': 0, 'reserved_quantity': 0, 'damaged_quantity': 0}
                )
                inventory_record.total_quantity = max(0, inventory_record.total_quantity - qty_deduct)
                inventory_record.save()

                # Sync recommendations status
                # If product depleted from this bin to 0: mark matching bin allocations as ALLOCATED
                bin_obj.refresh_from_db()
                final_bin_qty = sum(a.quantity for a in StorageAllocation.objects.filter(product=product, bin=bin_obj))
                from apps.recommendations.models.bin_allocation import BinAllocation
                bin_allocs = BinAllocation.objects.filter(product=product, bin=bin_obj)
                if final_bin_qty == 0:
                    for ba in bin_allocs:
                        ba.storage_status = BinAllocation.StorageStatus.ALLOCATED
                        ba.save()

                # Sync Digital Twin
                is_occupied = StorageAllocation.objects.filter(bin=bin_obj).exists()
                DigitalTwinSyncService.sync_occupancy(
                    bin_id=bin_obj.id,
                    is_occupied=is_occupied,
                    capacity_delta=-Decimal(str(qty_deduct))
                )

                # Log StockMovement
                StockMovement.objects.create(
                    product=product,
                    from_bin=bin_obj,
                    to_bin=None,
                    quantity=qty_deduct,
                    movement_type='DISPATCH',
                    operator=shipment.picklist.get("picker") or "operator"
                )

                # Log AuditTrail
                AuditLog.objects.create(
                    user=request.user,
                    action_type='DISPATCH_ITEM',
                    table_name='storage_allocations',
                    record_id=bin_obj.id
                )

            shipment.picklist["status"] = "DISPATCHED"
            shipment.status = "DISPATCHED"
            shipment.save()

        return Response({
            "success": True,
            "picklist_id": str(shipment.id),
            "status": "DISPATCHED",
            "message": "Shipment dispatched successfully. Inventory and allocations updated."
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='close')
    def close(self, request):
        """
        POST /api/orders/close/
        Closes shipment and finalizes logs.
        """
        serializer = OutboundOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        shipment = get_shipment(serializer.validated_data['picklist_id'])
        if not shipment:
            return Response({"error": "Shipment/Picklist not found"}, status=status.HTTP_404_NOT_FOUND)

        if not shipment.picklist:
            return Response({"error": "Picklist not generated yet"}, status=status.HTTP_400_BAD_REQUEST)

        shipment.picklist["status"] = "CLOSED"
        shipment.status = "CLOSED"
        shipment.dispatch_time = timezone.now()
        shipment.save()

        AuditLog.objects.create(
            user=request.user,
            action_type='SHIPMENT_CLOSE',
            table_name='outbound_shipments',
            record_id=shipment.id
        )

        return Response({
            "success": True,
            "shipment_code": shipment.shipment_code,
            "customer_name": shipment.customer_name,
            "dispatch_time": shipment.dispatch_time,
            "status": "CLOSED",
            "message": "Shipment closed. Completion record finalized."
        }, status=status.HTTP_200_OK)
