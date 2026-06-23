import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from ...models.bin_allocation import BinAllocation
from ...presentation.serializers.bin_allocation_serializer import BinAllocationOutputSerializer
from apps.inventory.infrastructure.persistence.models import Inventory, StockMovement
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)



class BinAllocationCompleteView(APIView):
    """
    PATCH /api/recommendations/bin-allocation/{id}/complete/
    Request:
    {
      "operator": "warehouse_operator_01"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk=None):
        logger.info("BinAllocationCompleteView: Complete request received for ID %s", pk)
        
        try:
            allocation = BinAllocation.objects.get(id=pk)
        except (BinAllocation.DoesNotExist, ValueError):
            logger.error("BinAllocationCompleteView: BinAllocation not found with ID %s", pk)
            return Response({"error": "Bin allocation not found"}, status=status.HTTP_404_NOT_FOUND)

        if allocation.storage_status == BinAllocation.StorageStatus.STORED:
            return Response({"error": "Bin allocation is already completed/stored"}, status=status.HTTP_400_BAD_REQUEST)

        operator_val = request.data.get('operator')
        if not operator_val:
            return Response({"error": "operator is required"}, status=status.HTTP_400_BAD_REQUEST)

        product = allocation.product
        bin_obj = allocation.bin

        try:
            with transaction.atomic():
                # 1. Update BinAllocation
                allocation.storage_status = BinAllocation.StorageStatus.STORED
                allocation.stored_at = timezone.now()
                allocation.operator = operator_val
                allocation.save()

                qty_val = 1
                if allocation.inbound_line:
                    qty_val = allocation.inbound_line.quantity
                    
                    # Update inbound line
                    line = allocation.inbound_line
                    line.recommendation_status = 'STORED'
                    line.save()
                    
                    # Update shipment status
                    shipment = line.shipment
                    if shipment:
                        if not shipment.line_items.exclude(recommendation_status='STORED').exists():
                            shipment.status = 'STORED'
                        else:
                            shipment.status = 'PARTIALLY_STORED'
                        shipment.save()
                    
                    # Update associated putaway task
                    from apps.inbound.infrastructure.persistence.inbound_models import PutawayTask
                    PutawayTask.objects.filter(inbound_line=line).update(
                        status=PutawayTask.PutawayStatus.COMPLETED,
                        completed_at=timezone.now(),
                        operator=operator_val
                    )

                # 2. Update Bin and Sync Digital Twin metrics
                from apps.warehouse.application.services.digital_twin_sync_service import DigitalTwinSyncService
                DigitalTwinSyncService.sync_occupancy(
                    bin_id=bin_obj.id,
                    is_occupied=True,
                    capacity_delta=Decimal(str(qty_val))
                )

                # 3. Update Inventory
                inventory_record, _ = Inventory.objects.get_or_create(
                    product=product,
                    defaults={'total_quantity': 0, 'reserved_quantity': 0, 'damaged_quantity': 0}
                )
                inventory_record.total_quantity = inventory_record.total_quantity + qty_val
                inventory_record.save()

                # 4. Log Stock Movement
                StockMovement.objects.create(
                    product=product,
                    from_bin=None,
                    to_bin=bin_obj,
                    quantity=qty_val,
                    movement_type='INBOUND_STORAGE_COMPLETED',
                    operator=operator_val
                )

            logger.info("BinAllocationCompleteView: Database transaction committed successfully.")

        except Exception as e:
            logger.exception("BinAllocationCompleteView: Transaction failed, rolling back: %s", e)
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Return serialized allocation output
        serializer = BinAllocationOutputSerializer(allocation)
        return Response(serializer.data, status=status.HTTP_200_OK)

