import uuid
from django.db import models

class InboundShipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='inbound_id')
    shipment_code = models.CharField(max_length=100, unique=True)
    supplier_name = models.CharField(max_length=200)
    expected_arrival = models.DateTimeField()
    status = models.CharField(max_length=50) # RECEIVED, PARTIALLY_STORED, STORED, etc.
    ocr_document = models.ForeignKey(
        'OCRDocument',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='ocr_document_id',
        related_name='shipments'
    )

    class Meta:
        db_table = 'inbound_shipments'

    def __str__(self):
        return f"{self.shipment_code} - {self.supplier_name}"


class InboundShipmentLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='line_id')
    shipment = models.ForeignKey(InboundShipment, on_delete=models.CASCADE, related_name='line_items', db_column='shipment_id')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='inbound_lines', db_column='product_id', null=True, blank=True)
    sku = models.CharField(max_length=100)
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    dimensions = models.CharField(max_length=100, default='10x8x6 cm')
    storage_type = models.CharField(max_length=50, default='GENERAL')
    recommendation_status = models.CharField(max_length=50, default='WAITING_FOR_BIN_ASSIGNMENT')

    class Meta:
        db_table = 'inbound_shipment_lines'

    def __str__(self):
        return f"{self.shipment.shipment_code} - {self.sku} ({self.quantity})"


class PutawayTask(models.Model):
    class PutawayStatus(models.TextChoices):
        ASSIGNED = 'ASSIGNED', 'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        PICKED_FROM_RECEIVING = 'PICKED_FROM_RECEIVING', 'Picked From Receiving'
        REACHED_BIN = 'REACHED_BIN', 'Reached Bin'
        COMPLETED = 'COMPLETED', 'Completed'
        DELAYED = 'DELAYED', 'Delayed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='task_id')
    operator = models.CharField(max_length=150, blank=True, null=True)
    inbound_shipment = models.ForeignKey(InboundShipment, on_delete=models.CASCADE, related_name='putaway_tasks', db_column='inbound_id', null=True, blank=True)
    inbound_line = models.ForeignKey(InboundShipmentLine, on_delete=models.CASCADE, related_name='putaway_tasks', db_column='line_id', null=True, blank=True)
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='putaway_tasks', db_column='product_id')
    quantity = models.IntegerField()
    source_dock = models.CharField(max_length=100, default='Receiving Dock')
    destination_bin = models.ForeignKey('warehouse.Bin', on_delete=models.CASCADE, related_name='putaway_tasks', db_column='bin_id')
    status = models.CharField(max_length=50, choices=PutawayStatus.choices, default=PutawayStatus.ASSIGNED)
    issue_type = models.CharField(max_length=100, blank=True, null=True)
    issue_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'putaway_tasks'

    def __str__(self):
        return f"PutawayTask {self.id} - {self.product.sku} ({self.status})"


