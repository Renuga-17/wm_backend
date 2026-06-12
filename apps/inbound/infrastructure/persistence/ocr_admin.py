from django.contrib import admin
from .ocr_models import OCRDocument


@admin.register(OCRDocument)
class OCRDocumentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'document_type', 'processing_status', 'confidence_score', 'created_at')
    list_filter = ('processing_status', 'document_type')
    search_fields = ('file_name', 'file_path', 'document_hash')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

