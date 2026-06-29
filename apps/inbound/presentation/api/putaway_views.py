import logging
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.inbound.infrastructure.persistence.inbound_models import InboundShipment, InboundShipmentLine, PutawayTask
from apps.inventory.infrastructure.persistence.models import Product, Inventory
from apps.inventory.infrastructure.persistence.movement_models import StockMovement
from apps.warehouse.infrastructure.persistence.models import Bin
from apps.recommendations.models.bin_allocation import BinAllocation

logger = logging.getLogger(__name__)

class PutawayTaskViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing Putaway tasks.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PutawayTask.objects.all().select_related(
            'inbound_shipment',
            'product',
            'inbound_line',
            'destination_bin__shelf__rack__zone'
        ).prefetch_related(
            'inbound_line__bin_allocations'
        ).order_by('-created_at')

    def get_serializer_class(self):
        # We don't necessarily need complex serializers since the payloads are simple.
        # But we will write custom representations below.
        return None

    def list(self, request, *args, **kwargs):
        """GET /api/inbound/putaway/"""
        status_filter = request.query_params.get('status')
        queryset = self.get_queryset()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        data = [self._serialize_task(t) for t in queryset]
        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """GET /api/inbound/putaway/{id}/"""
        try:
            task = PutawayTask.objects.get(id=pk)
            return Response(self._serialize_task(task), status=status.HTTP_200_OK)
        except (PutawayTask.DoesNotExist, ValueError):
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='assigned')
    def assigned(self, request):
        """GET /api/inbound/putaway/assigned/"""
        # Return tasks assigned to the current user or in non-completed status
        queryset = self.get_queryset().exclude(status=PutawayTask.PutawayStatus.COMPLETED)
        data = [self._serialize_task(t) for t in queryset]
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='dispatch')
    def dispatch_task(self, request):
        """
        POST /api/inbound/putaway/dispatch/
        Payload:
        {
          "operator": "staff@warehouseai.com",
          "inbound_line_id": "UUID",
          "destination_bin_id": "UUID" (optional)
        }
        """
        operator = request.data.get('operator')
        inbound_line_id = request.data.get('inbound_line_id') or request.data.get('inbound_id') # handle both key names
        destination_bin_id = request.data.get('destination_bin_id') or request.data.get('bin_id')

        if not inbound_line_id:
            return Response({"error": "inbound_line_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            line = InboundShipmentLine.objects.get(id=inbound_line_id)
        except (InboundShipmentLine.DoesNotExist, ValueError):
            # Try to resolve as InboundShipment ID and pick the first line
            try:
                shipment = InboundShipment.objects.get(id=inbound_line_id)
                line = shipment.line_items.first()
                if not line:
                    return Response({"error": "No line items found for the inbound shipment"}, status=status.HTTP_400_BAD_REQUEST)
            except (InboundShipment.DoesNotExist, ValueError):
                return Response({"error": "Inbound line or shipment not found"}, status=status.HTTP_404_NOT_FOUND)

        # Resolve destination bin
        bin_obj = None
        if destination_bin_id:
            try:
                bin_obj = Bin.objects.get(id=destination_bin_id)
            except (Bin.DoesNotExist, ValueError):
                bin_obj = Bin.objects.filter(bin_code=destination_bin_id).first()
        
        # If no destination bin provided, check latest BinAllocation
        allocation = BinAllocation.objects.filter(inbound_line=line).order_by('-created_at').first()
        if not bin_obj and allocation:
            bin_obj = allocation.bin

        if not bin_obj:
            # Fallback to any active bin if nothing found
            bin_obj = Bin.objects.filter(is_occupied=False).first() or Bin.objects.first()

        if not bin_obj:
            return Response({"error": "No available bins found for putaway"}, status=status.HTTP_400_BAD_REQUEST)

        # Create putaway task atomically
        with transaction.atomic():
            task = PutawayTask.objects.create(
                operator=operator or request.user.username,
                inbound_shipment=line.shipment,
                inbound_line=line,
                product=line.product,
                quantity=line.quantity,
                destination_bin=bin_obj,
                status=PutawayTask.PutawayStatus.ASSIGNED
            )

            # Update allocation status to IN_PROGRESS
            if allocation:
                allocation.storage_status = BinAllocation.StorageStatus.IN_PROGRESS
                allocation.operator = operator or request.user.username
                allocation.save()

            # Update line status to RECOMMENDED/IN_PROGRESS
            line.recommendation_status = 'RECOMMENDED'
            line.save()

        return Response(self._serialize_task(task), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='start')
    def start_task(self, request, pk=None):
        """POST /api/inbound/putaway/{id}/start/"""
        task = self.get_object()
        task.status = PutawayTask.PutawayStatus.IN_PROGRESS
        task.save()
        
        # Update allocation status if available
        if task.inbound_line:
            alloc = BinAllocation.objects.filter(inbound_line=task.inbound_line).first()
            if alloc:
                alloc.storage_status = BinAllocation.StorageStatus.IN_PROGRESS
                alloc.save()
                
        return Response(self._serialize_task(task), status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='picked')
    def picked_task(self, request, pk=None):
        """POST /api/inbound/putaway/{id}/picked/"""
        task = self.get_object()
        task.status = PutawayTask.PutawayStatus.PICKED_FROM_RECEIVING
        task.save()
        return Response(self._serialize_task(task), status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reached')
    def reached_task(self, request, pk=None):
        """POST /api/inbound/putaway/{id}/reached/"""
        task = self.get_object()
        task.status = PutawayTask.PutawayStatus.REACHED_BIN
        task.save()
        return Response(self._serialize_task(task), status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'patch'], url_path='complete')
    def complete_task(self, request, pk=None):
        """
        POST or PATCH /api/inbound/putaway/{id}/complete/
        """
        try:
            task = PutawayTask.objects.get(id=pk)
        except (PutawayTask.DoesNotExist, ValueError):
            return Response({"error": "Putaway task not found"}, status=status.HTTP_404_NOT_FOUND)

        if task.status == PutawayTask.PutawayStatus.COMPLETED:
            return Response(self._serialize_task(task), status=status.HTTP_200_OK)

        # Confirm operator completing task
        operator = request.data.get('operator') or task.operator or request.user.username

        with transaction.atomic():
            # 1. Update task
            task.status = PutawayTask.PutawayStatus.COMPLETED
            task.completed_at = timezone.now()
            task.operator = operator
            task.save()

            # 2. Update Inbound Line & Inbound Shipment status
            if task.inbound_line:
                task.inbound_line.recommendation_status = 'STORED'
                task.inbound_line.save()
                
                # Check if all lines are stored
                shipment = task.inbound_shipment
                if shipment:
                    if not shipment.line_items.exclude(recommendation_status='STORED').exists():
                        shipment.status = 'STORED'
                    else:
                        shipment.status = 'PARTIALLY_STORED'
                    shipment.save()

            # 3. Update inventory table
            inventory_record, _ = Inventory.objects.get_or_create(
                product=task.product,
                defaults={'total_quantity': 0, 'reserved_quantity': 0, 'damaged_quantity': 0}
            )
            inventory_record.total_quantity += task.quantity
            inventory_record.save()

            # 4. Create stock_movement row
            StockMovement.objects.create(
                product=task.product,
                from_bin=None,
                to_bin=task.destination_bin,
                quantity=task.quantity,
                movement_type='PUTAWAY_COMPLETED',
                operator=operator
            )

            # 5. Update bin current_capacity & occupied state
            bin_obj = task.destination_bin
            bin_obj.current_capacity = min(bin_obj.max_capacity, bin_obj.current_capacity + Decimal(str(task.quantity)))
            bin_obj.is_occupied = True
            bin_obj.save()

            # 6. Update BinAllocation status if exists
            if task.inbound_line:
                alloc = BinAllocation.objects.filter(inbound_line=task.inbound_line).first()
                if alloc:
                    alloc.storage_status = BinAllocation.StorageStatus.STORED
                    alloc.stored_at = timezone.now()
                    alloc.operator = operator
                    alloc.save()

        return Response(self._serialize_task(task), status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='issue')
    def report_issue(self, request, pk=None):
        """POST /api/inbound/putaway/{id}/issue/"""
        task = self.get_object()
        issue_type = request.data.get('issue_type') or request.data.get('issue')
        issue_desc = request.data.get('description') or request.data.get('notes')

        task.status = PutawayTask.PutawayStatus.DELAYED
        task.issue_type = issue_type or "Handling Issue"
        task.issue_description = issue_desc or "No details provided"
        task.save()

        # Log movement as issue
        StockMovement.objects.create(
            product=task.product,
            from_bin=None,
            to_bin=task.destination_bin,
            quantity=task.quantity,
            movement_type='PUTAWAY_ISSUE_REPORTED',
            operator=task.operator or request.user.username
        )

        return Response(self._serialize_task(task), status=status.HTTP_200_OK)

    def _serialize_task(self, task):
        # Build compatibility payload for frontend mapping
        # Frontend expects: id, inboundId, sku, product, quantity, priority, status, pickupLocation, destinationBin, etc.
        alloc = None
        if task.inbound_line:
            # Use prefetch cache if available to resolve N+1 queries
            if hasattr(task.inbound_line, '_prefetched_objects_cache') and 'bin_allocations' in task.inbound_line._prefetched_objects_cache:
                allocs = list(task.inbound_line.bin_allocations.all())
                if allocs:
                    alloc = allocs[0]
            else:
                alloc = BinAllocation.objects.filter(inbound_line=task.inbound_line).order_by('-created_at').first()
        
        issue_payload = None
        if task.issue_type:
            issue_payload = {
                "issueType": task.issue_type,
                "description": task.issue_description,
                "reportedBy": task.operator or "Operator",
                "reportedAt": task.updated_at.isoformat() if task.updated_at else None
            }
        
        return {
            "id": str(task.id),
            "inboundId": str(task.inbound_shipment.id) if task.inbound_shipment else None,
            "sku": task.product.sku,
            "product": task.product.product_name,
            "quantity": task.quantity,
            "priority": "High" if task.quantity > 100 else "Medium",
            "status": task.status,
            "pickupLocation": task.source_dock,
            "destinationBin": task.destination_bin.bin_code if task.destination_bin else None,
            "destinationZone": task.destination_bin.shelf.rack.zone.zone_name if task.destination_bin else "Zone A",
            "destinationRack": task.destination_bin.shelf.rack.rack_code if task.destination_bin else "Rack 1",
            "destinationShelf": f"Level {task.destination_bin.shelf.shelf_number}" if task.destination_bin else "Level 1",
            "bin": task.destination_bin.bin_code if task.destination_bin else None,
            "routePath": alloc.navigation_instructions if alloc else "Dock -> Zone",
            "orientation": alloc.selected_orientation if alloc else None,
            "maxUnitsFit": alloc.max_units if alloc else None,
            "utilizationScore": alloc.utilization_score if alloc else None,
            "recommendationReason": alloc.allocation_reason if alloc else None,
            "placementInstruction": alloc.placement_instructions if alloc else None,
            "estTime": "5 mins",
            "distance": "45 meters",
            "operator": task.operator,
            "issue": issue_payload,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None

        }
