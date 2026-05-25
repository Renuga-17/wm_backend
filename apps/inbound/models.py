import uuid
from django.db import models

class InboundShipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='inbound_id')
    shipment_code = models.CharField(max_length=100, unique=True)
    supplier_name = models.CharField(max_length=200)
    expected_arrival = models.DateTimeField()
    status = models.CharField(max_length=50)

    class Meta:
        db_table = 'inbound_shipments'

    def __str__(self):
        return f"{self.shipment_code} - {self.supplier_name}"

