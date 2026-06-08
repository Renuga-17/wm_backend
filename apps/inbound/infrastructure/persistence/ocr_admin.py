from django.contrib import admin
from .models import OCRDocument


@admin.register(OCRDocument)
class OCRDocumentAdmin(admin.ModelAdmin):
    list_display = ('document_name', 'document_type', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'document_type')
    search_fields = ('document_name', 'document_url')
    readonly_fields = ('id', 'extracted_text', 'structured_data', 'created_at', 'updated_at')
    ordering = ('-created_at',)
