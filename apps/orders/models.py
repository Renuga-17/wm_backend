import uuid
from django.db import models

class OutboundShipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='outbound_id')
    shipment_code = models.CharField(max_length=100, unique=True)
    customer_name = models.CharField(max_length=200)
    dispatch_time = models.DateTimeField()
    status = models.CharField(max_length=50)

    class Meta:
        db_table = 'outbound_shipments'

    def __str__(self):
        return f"{self.shipment_code} - {self.customer_name}"

