<<<<<<< HEAD
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone
from decimal import Decimal

from apps.inventory.infrastructure.persistence.models import (
    Inventory, Product, ProductDimension, StockMovement, StorageAllocation
)
from apps.warehouse.infrastructure.persistence.models import Bin
from apps.identity.infrastructure.persistence.models import AuditLog
from apps.recommendations.models.bin_allocation import BinAllocation
from apps.warehouse.application.services.digital_twin_sync_service import DigitalTwinSyncService
from apps.recommendations.services.dimension_compatibility_service import DimensionCompatibilityService

from .serializers import (
    InventorySerializer,
    ProductRelocationSerializer,
    BinTransferSerializer,
    StockAdjustmentSerializer,
    DamageReportSerializer,
    InventoryAuditSerializer
)

from django.core.exceptions import ValidationError
from common.permissions import ReadOnlyOrAuthenticated

def get_bin(bin_id):
    try:
        return Bin.objects.get(id=bin_id)
    except (Bin.DoesNotExist, ValueError, ValidationError):
        return Bin.objects.filter(bin_code=bin_id).first()

def get_product(product_id):
    try:
        return Product.objects.get(id=product_id)
    except (Product.DoesNotExist, ValueError, ValidationError):
        return Product.objects.filter(sku=product_id).first()

def sync_bin_allocation_status(product, bin, current_quantity, operator=""):
    """
    Ensures consistency between StorageAllocation quantity and BinAllocation status.
    - If current_quantity > 0: ensure a STORED BinAllocation exists.
    - If current_quantity == 0: set matching STORED BinAllocation storage_status to ALLOCATED.
    """
    bin_allocs = BinAllocation.objects.filter(product=product, bin=bin)
    if current_quantity > 0:
        if bin_allocs.exists():
            for ba in bin_allocs:
                if ba.storage_status != BinAllocation.StorageStatus.STORED:
                    ba.storage_status = BinAllocation.StorageStatus.STORED
                    ba.stored_at = ba.stored_at or timezone.now()
                    ba.operator = ba.operator or operator
                    ba.save()
        else:
            # Create a fallback BinAllocation record representing current inventory state
            zone = bin.shelf.rack.zone
            zone_group = zone.zone_group
            BinAllocation.objects.create(
                product=product,
                zone_group=zone_group,
                zone=zone,
                rack=bin.shelf.rack,
                shelf=bin.shelf,
                bin=bin,
                allocation_score=1.0,
                allocation_reason="Automatically synced from inventory operation",
                selected_orientation="L×W×H",
                storage_status=BinAllocation.StorageStatus.STORED,
                stored_at=timezone.now(),
                operator=operator
            )
    else:
        # Stock depleted to 0: mark matching bin allocations as ALLOCATED
        for ba in bin_allocs:
            ba.storage_status = BinAllocation.StorageStatus.ALLOCATED
            ba.save()

def sync_inventory_total(product):
    """
    Ensures that the Inventory record's total_quantity matches the sum of all its StorageAllocation quantities.
    """
    total_alloc_qty = StorageAllocation.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
    inventory_record, _ = Inventory.objects.get_or_create(
        product=product,
        defaults={'total_quantity': 0, 'reserved_quantity': 0, 'damaged_quantity': 0}
    )
    if inventory_record.total_quantity != total_alloc_qty:
        inventory_record.total_quantity = total_alloc_qty
        inventory_record.save()
    return inventory_record


class InventoryViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = Inventory.objects.all()
=======
from rest_framework import viewsets
from django.db.models import Prefetch
from apps.inventory.infrastructure.persistence.models import Inventory, StorageAllocation
from .serializers import InventorySerializer

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all().select_related(
        'product',
        'product__category'
    ).prefetch_related(
        'product__dimensions',
        Prefetch(
            'product__allocations',
            queryset=StorageAllocation.objects.all().select_related(
                'bin',
                'bin__shelf',
                'bin__shelf__rack',
                'bin__shelf__rack__zone',
                'bin__shelf__rack__zone__warehouse'
            )
        )
    )
>>>>>>> aa8d66f5b9fd6bb95bb4e3703639135fd7dc4ec4
    serializer_class = InventorySerializer

    @action(detail=False, methods=['post'], url_path='relocate')
    def relocate(self, request):
        """
        POST /api/inventory/relocate/
        Relocates quantity of a product from from_bin to to_bin.
        """
        serializer = ProductRelocationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        product = get_product(data['product_id'])
        from_bin = get_bin(data['from_bin_id'])
        to_bin = get_bin(data['to_bin_id'])
        quantity = data['quantity']
        operator_val = data.get('operator') or request.user.username or 'operator'

        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        if not from_bin:
            return Response({"error": "Source bin not found"}, status=status.HTTP_404_NOT_FOUND)
        if not to_bin:
            return Response({"error": "Target bin not found"}, status=status.HTTP_404_NOT_FOUND)
        if from_bin.id == to_bin.id:
            return Response({"error": "Source and target bins cannot be the same"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Validate inventory
        from_allocations = StorageAllocation.objects.filter(product=product, bin=from_bin)
        from_qty = sum(a.quantity for a in from_allocations)
        if from_qty < quantity:
            return Response(
                {"error": f"Insufficient stock in bin {from_bin.bin_code}. Available: {from_qty}, Requested: {quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Validate capacity
        added_qty = Decimal(str(quantity))
        if to_bin.current_capacity + added_qty > to_bin.max_capacity:
            return Response(
                {"error": f"Target bin {to_bin.bin_code} capacity exceeded. Max: {to_bin.max_capacity}, Current: {to_bin.current_capacity}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Validate dimensions
        dim = ProductDimension.objects.filter(product=product).first()
        if not dim:
            return Response(
                {"error": f"Product dimensions not configured for product {product.sku}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        compat_service = DimensionCompatibilityService()
        compat = compat_service.check_compatibility(
            product_len=dim.length,
            product_width=dim.width,
            product_height=dim.height,
            bin_len=to_bin.length,
            bin_width=to_bin.width,
            bin_height=to_bin.height
        )
        if not compat['fits']:
            return Response(
                {"error": f"Product dimensions do not fit inside bin {to_bin.bin_code}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Validate weight limits
        shelf = to_bin.shelf
        rack = shelf.rack

        shelf_weight = StorageAllocation.objects.filter(bin__shelf=shelf).aggregate(
            total_w=Sum(F('quantity') * F('product__weight'))
        )['total_w'] or Decimal('0.00')

        rack_weight = StorageAllocation.objects.filter(bin__shelf__rack=rack).aggregate(
            total_w=Sum(F('quantity') * F('product__weight'))
        )['total_w'] or Decimal('0.00')

        added_weight = Decimal(str(product.weight)) * added_qty

        # Compensate if from_bin and to_bin share the same shelf/rack
        projected_shelf_weight = shelf_weight
        if from_bin.shelf_id != to_bin.shelf_id:
            projected_shelf_weight += added_weight

        projected_rack_weight = rack_weight
        if from_bin.shelf.rack_id != to_bin.shelf.rack_id:
            projected_rack_weight += added_weight

        if projected_shelf_weight > shelf.max_weight:
            return Response(
                {"error": f"Shelf weight capacity exceeded. Max: {shelf.max_weight}, Projected: {projected_shelf_weight}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if projected_rack_weight > rack.max_weight:
            return Response(
                {"error": f"Rack weight capacity exceeded. Max: {rack.max_weight}, Projected: {projected_rack_weight}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Apply transfer atomically
        with transaction.atomic():
            # Deduct allocations
            remaining_to_deduct = quantity
            for alloc in from_allocations.order_by('allocated_at'):
                if alloc.quantity > remaining_to_deduct:
                    alloc.quantity -= remaining_to_deduct
                    alloc.save()
                    remaining_to_deduct = 0
                    break
                else:
                    remaining_to_deduct -= alloc.quantity
                    alloc.delete()

            # Add to target allocation
            to_alloc, _ = StorageAllocation.objects.get_or_create(
                product=product,
                bin=to_bin,
                defaults={'quantity': 0}
            )
            to_alloc.quantity += quantity
            to_alloc.save()

            # Update Digital Twin sync and local capacities
            from_is_occupied = (from_bin.current_capacity - added_qty) > 0
            DigitalTwinSyncService.sync_occupancy(
                bin_id=from_bin.id,
                is_occupied=from_is_occupied,
                capacity_delta=-added_qty
            )

            DigitalTwinSyncService.sync_occupancy(
                bin_id=to_bin.id,
                is_occupied=True,
                capacity_delta=added_qty
            )

            # Sync BinAllocation statuses
            from_bin.refresh_from_db()
            to_bin.refresh_from_db()
            from_final_qty = sum(a.quantity for a in StorageAllocation.objects.filter(product=product, bin=from_bin))
            to_final_qty = sum(a.quantity for a in StorageAllocation.objects.filter(product=product, bin=to_bin))
            sync_bin_allocation_status(product, from_bin, from_final_qty, operator_val)
            sync_bin_allocation_status(product, to_bin, to_final_qty, operator_val)

            # Sync global Inventory total
            sync_inventory_total(product)

            # Log stock movement
            StockMovement.objects.create(
                product=product,
                from_bin=from_bin,
                to_bin=to_bin,
                quantity=quantity,
                movement_type='RELOCATION',
                operator=operator_val
            )

            # Audit log
            AuditLog.objects.create(
                user=request.user,
                action_type='RELOCATION',
                table_name='stock_movements',
                record_id=to_alloc.id
            )

        return Response({"success": True, "message": f"Successfully relocated {quantity} items of {product.sku} to {to_bin.bin_code}"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='transfer')
    def transfer(self, request):
        """
        POST /api/inventory/transfer/
        Transfers stock between bins. Performs full validations.
        """
        serializer = BinTransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Delegate logic directly to relocate (relocate is a validated transfer)
        # We reuse the relocate logic to avoid duplicate code while ensuring all limits are checked.
        # Rename the fields from BinTransferSerializer to match ProductRelocationSerializer payload
        payload = {
            "product_id": serializer.validated_data["product_id"],
            "from_bin_id": serializer.validated_data["from_bin_id"],
            "to_bin_id": serializer.validated_data["to_bin_id"],
            "quantity": serializer.validated_data["quantity"],
            "operator": serializer.validated_data.get("operator")
        }
        
        # Execute relocation with custom audit trail types
        product = get_product(payload['product_id'])
        from_bin = get_bin(payload['from_bin_id'])
        to_bin = get_bin(payload['to_bin_id'])
        quantity = payload['quantity']
        operator_val = payload.get('operator') or request.user.username or 'operator'

        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        if not from_bin:
            return Response({"error": "Source bin not found"}, status=status.HTTP_404_NOT_FOUND)
        if not to_bin:
            return Response({"error": "Target bin not found"}, status=status.HTTP_404_NOT_FOUND)

        # 1. Validate inventory
        from_allocations = StorageAllocation.objects.filter(product=product, bin=from_bin)
        from_qty = sum(a.quantity for a in from_allocations)
        if from_qty < quantity:
            return Response(
                {"error": f"Insufficient stock in bin {from_bin.bin_code}. Available: {from_qty}, Requested: {quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Validate capacity
        added_qty = Decimal(str(quantity))
        if to_bin.current_capacity + added_qty > to_bin.max_capacity:
            return Response(
                {"error": f"Target bin {to_bin.bin_code} capacity exceeded. Max: {to_bin.max_capacity}, Current: {to_bin.current_capacity}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Apply transfer atomically
        with transaction.atomic():
            # Deduct allocations
            remaining_to_deduct = quantity
            for alloc in from_allocations.order_by('allocated_at'):
                if alloc.quantity > remaining_to_deduct:
                    alloc.quantity -= remaining_to_deduct
                    alloc.save()
                    remaining_to_deduct = 0
                    break
                else:
                    remaining_to_deduct -= alloc.quantity
                    alloc.delete()

            # Add to target allocation
            to_alloc, _ = StorageAllocation.objects.get_or_create(
                product=product,
                bin=to_bin,
                defaults={'quantity': 0}
            )
            to_alloc.quantity += quantity
            to_alloc.save()

            # Update capacities
            from_is_occupied = (from_bin.current_capacity - added_qty) > 0
            DigitalTwinSyncService.sync_occupancy(
                bin_id=from_bin.id,
                is_occupied=from_is_occupied,
                capacity_delta=-added_qty
            )

            DigitalTwinSyncService.sync_occupancy(
                bin_id=to_bin.id,
                is_occupied=True,
                capacity_delta=added_qty
            )

            # Sync recommendations
            from_bin.refresh_from_db()
            to_bin.refresh_from_db()
            from_final_qty = sum(a.quantity for a in StorageAllocation.objects.filter(product=product, bin=from_bin))
            to_final_qty = sum(a.quantity for a in StorageAllocation.objects.filter(product=product, bin=to_bin))
            sync_bin_allocation_status(product, from_bin, from_final_qty, operator_val)
            sync_bin_allocation_status(product, to_bin, to_final_qty, operator_val)

            # Sync global Inventory total
            sync_inventory_total(product)

            # Log stock movement
            StockMovement.objects.create(
                product=product,
                from_bin=from_bin,
                to_bin=to_bin,
                quantity=quantity,
                movement_type='BIN_TRANSFER',
                operator=operator_val
            )

            # Audit log
            AuditLog.objects.create(
                user=request.user,
                action_type='BIN_TRANSFER',
                table_name='stock_movements',
                record_id=to_alloc.id
            )

        return Response({"success": True, "message": f"Successfully transferred {quantity} of {product.sku} to {to_bin.bin_code}"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='adjust')
    def adjust(self, request):
        """
        POST /api/inventory/adjust/
        Cycles count adjustments. Supports positive and negative deltas.
        """
        serializer = StockAdjustmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        product = get_product(data['product_id'])
        bin_obj = get_bin(data['bin_id'])
        quantity = data['quantity']
        reason = data.get('reason') or 'Manual adjustment'
        operator_val = data.get('operator') or request.user.username or 'operator'

        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        if not bin_obj:
            return Response({"error": "Bin not found"}, status=status.HTTP_404_NOT_FOUND)
        if quantity == 0:
            return Response({"error": "Adjustment quantity cannot be zero"}, status=status.HTTP_400_BAD_REQUEST)

        allocations = StorageAllocation.objects.filter(product=product, bin=bin_obj)
        current_qty = sum(a.quantity for a in allocations)

        if quantity < 0 and current_qty < abs(quantity):
            return Response(
                {"error": f"Cannot adjust below zero. Current quantity: {current_qty}, Deducting: {abs(quantity)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        delta_dec = Decimal(str(quantity))
        # If adding stock, validate capacity
        if quantity > 0 and bin_obj.current_capacity + delta_dec > bin_obj.max_capacity:
            return Response(
                {"error": f"Capacity limit exceeded for bin {bin_obj.bin_code}. Max: {bin_obj.max_capacity}, Current: {bin_obj.current_capacity}, Adding: {delta_dec}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Update StorageAllocation
            if quantity > 0:
                to_alloc, _ = StorageAllocation.objects.get_or_create(
                    product=product,
                    bin=bin_obj,
                    defaults={'quantity': 0}
                )
                to_alloc.quantity += quantity
                to_alloc.save()
                record_id = to_alloc.id
            else:
                remaining_to_deduct = abs(quantity)
                record_id = None
                for alloc in allocations.order_by('allocated_at'):
                    record_id = alloc.id
                    if alloc.quantity > remaining_to_deduct:
                        alloc.quantity -= remaining_to_deduct
                        alloc.save()
                        remaining_to_deduct = 0
                        break
                    else:
                        remaining_to_deduct -= alloc.quantity
                        alloc.delete()

            # Sync global Inventory total
            sync_inventory_total(product)

            # Update Digital Twin capacities
            new_capacity = bin_obj.current_capacity + delta_dec
            is_occupied = new_capacity > 0
            DigitalTwinSyncService.sync_occupancy(
                bin_id=bin_obj.id,
                is_occupied=is_occupied,
                capacity_delta=delta_dec
            )

            # Sync recommendations
            bin_obj.refresh_from_db()
            final_qty = sum(a.quantity for a in StorageAllocation.objects.filter(product=product, bin=bin_obj))
            sync_bin_allocation_status(product, bin_obj, final_qty, operator_val)

            # Log movement
            m_type = 'STOCK_ADJUSTMENT_INCREASE' if quantity > 0 else 'STOCK_ADJUSTMENT_DECREASE'
            movement = StockMovement.objects.create(
                product=product,
                from_bin=bin_obj if quantity < 0 else None,
                to_bin=bin_obj if quantity > 0 else None,
                quantity=abs(quantity),
                movement_type=m_type,
                operator=f"{operator_val} ({reason})"
            )

            # Audit log
            AuditLog.objects.create(
                user=request.user,
                action_type=m_type,
                table_name='inventory',
                record_id=record_id or movement.id
            )

        return Response({"success": True, "message": f"Successfully adjusted inventory count by {quantity} for {product.sku} in bin {bin_obj.bin_code}."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='report-damage')
    def report_damage(self, request):
        """
        POST /api/inventory/report-damage/
        Moves quantity from active good stock to damaged stock.
        """
        serializer = DamageReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        product = get_product(data['product_id'])
        bin_obj = get_bin(data['bin_id'])
        quantity = data['quantity']
        reason = data.get('reason') or 'Damaged'
        operator_val = data.get('operator') or request.user.username or 'operator'

        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        if not bin_obj:
            return Response({"error": "Bin not found"}, status=status.HTTP_404_NOT_FOUND)

        allocations = StorageAllocation.objects.filter(product=product, bin=bin_obj)
        current_qty = sum(a.quantity for a in allocations)

        if current_qty < quantity:
            return Response(
                {"error": f"Insufficient stock in bin {bin_obj.bin_code} to report damage. Available: {current_qty}, Requested: {quantity}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        dec_qty = Decimal(str(quantity))

        with transaction.atomic():
            # 1. Deduct allocations
            remaining_to_deduct = quantity
            record_id = None
            for alloc in allocations.order_by('allocated_at'):
                record_id = alloc.id
                if alloc.quantity > remaining_to_deduct:
                    alloc.quantity -= remaining_to_deduct
                    alloc.save()
                    remaining_to_deduct = 0
                    break
                else:
                    remaining_to_deduct -= alloc.quantity
                    alloc.delete()

            # 2. Sync global Inventory (and add to damaged_quantity)
            inventory_record = sync_inventory_total(product)
            inventory_record.damaged_quantity += quantity
            inventory_record.save()

            # 3. Update capacities
            new_capacity = bin_obj.current_capacity - dec_qty
            is_occupied = new_capacity > 0
            DigitalTwinSyncService.sync_occupancy(
                bin_id=bin_obj.id,
                is_occupied=is_occupied,
                capacity_delta=-dec_qty
            )

            # 4. Sync recommendations status
            bin_obj.refresh_from_db()
            final_qty = sum(a.quantity for a in StorageAllocation.objects.filter(product=product, bin=bin_obj))
            sync_bin_allocation_status(product, bin_obj, final_qty, operator_val)

            # 5. Log stock movement
            StockMovement.objects.create(
                product=product,
                from_bin=bin_obj,
                to_bin=None,
                quantity=quantity,
                movement_type='DAMAGE_REPORT',
                operator=f"{operator_val} ({reason})"
            )

            # 6. Audit log
            AuditLog.objects.create(
                user=request.user,
                action_type='DAMAGE_REPORT',
                table_name='inventory',
                record_id=inventory_record.id
            )

        return Response({"success": True, "message": f"Reported {quantity} damaged items of {product.sku} from bin {bin_obj.bin_code}."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='audit')
    def audit(self, request):
        """
        POST /api/inventory/audit/
        Handles physical stock count check, variance calculations, and reconciliation.
        """
        serializer = InventoryAuditSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        product = get_product(data['product_id'])
        bin_obj = get_bin(data['bin_id'])
        physical_count = data['physical_count']
        reason = data.get('reason') or 'Stocktake audit'
        operator_val = data.get('operator') or request.user.username or 'operator'

        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        if not bin_obj:
            return Response({"error": "Bin not found"}, status=status.HTTP_404_NOT_FOUND)

        allocations = StorageAllocation.objects.filter(product=product, bin=bin_obj)
        system_count = sum(a.quantity for a in allocations)
        variance = physical_count - system_count

        if variance == 0:
            return Response({
                "success": True,
                "system_count": system_count,
                "physical_count": physical_count,
                "variance": 0,
                "status": "reconciled",
                "message": "Physical count matches system records. No adjustments needed."
            }, status=status.HTTP_200_OK)

        dec_variance = Decimal(str(variance))

        # Capacity checks for positive variance
        if variance > 0 and bin_obj.current_capacity + dec_variance > bin_obj.max_capacity:
            return Response(
                {"error": f"Reconciliation would overflow target bin {bin_obj.bin_code} capacity limits. Max: {bin_obj.max_capacity}, Current: {bin_obj.current_capacity}, Variance: {dec_variance}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Reconcile StorageAllocation
            if physical_count == 0:
                allocations.delete()
                record_id = bin_obj.id
            else:
                if system_count == 0:
                    # Create allocation
                    new_alloc = StorageAllocation.objects.create(
                        product=product,
                        bin=bin_obj,
                        quantity=physical_count
                    )
                    record_id = new_alloc.id
                else:
                    # Update quantity
                    first_alloc = allocations.first()
                    first_alloc.quantity = physical_count
                    first_alloc.save()
                    record_id = first_alloc.id
                    # Clean up other duplicate allocations if any
                    allocations.exclude(id=first_alloc.id).delete()

            # Sync global Inventory total
            sync_inventory_total(product)

            # Update capacities
            new_capacity = bin_obj.current_capacity + dec_variance
            is_occupied = new_capacity > 0
            DigitalTwinSyncService.sync_occupancy(
                bin_id=bin_obj.id,
                is_occupied=is_occupied,
                capacity_delta=dec_variance
            )

            # Sync recommendations status
            bin_obj.refresh_from_db()
            final_qty = sum(a.quantity for a in StorageAllocation.objects.filter(product=product, bin=bin_obj))
            sync_bin_allocation_status(product, bin_obj, final_qty, operator_val)

            # Log stock movement
            m_type = 'AUDIT_SURPLUS' if variance > 0 else 'AUDIT_LOSS'
            StockMovement.objects.create(
                product=product,
                from_bin=bin_obj if variance < 0 else None,
                to_bin=bin_obj if variance > 0 else None,
                quantity=abs(variance),
                movement_type=m_type,
                operator=f"{operator_val} ({reason})"
            )

            # Audit log
            AuditLog.objects.create(
                user=request.user,
                action_type='INVENTORY_AUDIT',
                table_name='inventory',
                record_id=record_id
            )

        return Response({
            "success": True,
            "system_count": system_count,
            "physical_count": physical_count,
            "variance": variance,
            "status": "adjusted",
            "message": f"Reconciliation adjustment performed. Stock adjusted by variance {variance}."
        }, status=status.HTTP_200_OK)
