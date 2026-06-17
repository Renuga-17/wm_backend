import logging
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

                # 2. Update Bin
                bin_obj.is_occupied = True
                bin_obj.save()

                # 3. Update Inventory
                inventory_record, _ = Inventory.objects.get_or_create(
                    product=product,
                    defaults={'total_quantity': 0, 'reserved_quantity': 0, 'damaged_quantity': 0}
                )
                inventory_record.total_quantity = inventory_record.total_quantity + 1
                inventory_record.save()

                # 4. Log Stock Movement
                StockMovement.objects.create(
                    product=product,
                    from_bin=None,
                    to_bin=bin_obj,
                    quantity=1,
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

        # 5. Broadcast Occupancy to Digital Twin WebSocket Consumer
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    'occupancy_updates',
                    {
                        'type': 'occupancy_message',
                        'message': {
                            'bin_code': bin_obj.bin_code,
                            'is_occupied': bin_obj.is_occupied,
                            'current_capacity': float(bin_obj.current_capacity)
                        }
                    }
                )
                logger.info("BinAllocationCompleteView: Websocket broadcast succeeded.")
        except Exception as ws_err:
            logger.warning("BinAllocationCompleteView: Websocket broadcast failed: %s", ws_err)

        # Return serialized allocation output
        serializer = BinAllocationOutputSerializer(allocation)
        return Response(serializer.data, status=status.HTTP_200_OK)
