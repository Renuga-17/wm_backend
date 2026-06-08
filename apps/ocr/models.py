import uuid
from django.db import models


class OCRDocument(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    class DocumentType(models.TextChoices):
        INVOICE = 'invoice', 'Invoice'
        PURCHASE_ORDER = 'po', 'Purchase Order'
        MANIFEST = 'manifest', 'Manifest'
        OTHER = 'other', 'Other'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        db_column='ocr_id'
    )
    document_name = models.CharField(max_length=200)
    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )
    document_url = models.URLField()
    extracted_text = models.TextField(blank=True, default='')
    structured_data = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ocr_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document_name} [{self.status}]"
