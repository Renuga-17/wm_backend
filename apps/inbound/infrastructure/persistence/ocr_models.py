import uuid
from django.db import models


class OCRDocument(models.Model):
    class ProcessingStatus(models.TextChoices):
        UPLOADED = 'UPLOADED', 'Uploaded'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REVIEW_REQUIRED = 'REVIEW_REQUIRED', 'Review Required'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        db_column='ocr_id'
    )
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=512)
    document_type = models.CharField(max_length=100)
    document_hash = models.CharField(max_length=64, blank=True, null=True)
    raw_text = models.TextField(blank=True, default='')
    extracted_json = models.JSONField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    processing_status = models.CharField(
        max_length=50,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.UPLOADED
    )
    error_message = models.TextField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # WMS Metadata fields for RAG
    warehouse_id = models.CharField(max_length=100, null=True, blank=True)
    sku = models.CharField(max_length=100, null=True, blank=True)
    product_id = models.CharField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    zone = models.CharField(max_length=100, null=True, blank=True)
    rack = models.CharField(max_length=100, null=True, blank=True)
    shelf = models.CharField(max_length=100, null=True, blank=True)
    bin = models.CharField(max_length=100, null=True, blank=True)
    chunk_count = models.IntegerField(default=0)
    rag_status = models.CharField(
        max_length=50,
        choices=[
            ('PENDING', 'Pending'),
            ('INGESTING', 'Ingesting'),
            ('INGESTED', 'Ingested'),
            ('FAILED', 'Failed')
        ],
        default='PENDING'
    )
    rag_error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'ocr_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.file_name} [{self.processing_status}]"

