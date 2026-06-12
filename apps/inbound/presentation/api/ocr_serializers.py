from rest_framework import serializers
from apps.inbound.infrastructure.persistence.models import OCRDocument


class OCRDocumentSerializer(serializers.ModelSerializer):
    document_id = serializers.UUIDField(source='id', read_only=True)
    status = serializers.CharField(source='processing_status', read_only=True)

    class Meta:
        model = OCRDocument
        fields = [
            'document_id',
            'status',
            'file_name',
            'file_path',
            'document_type',
            'document_hash',
            'raw_text',
            'extracted_json',
            'confidence_score',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = (
            'document_id',
            'status',
            'raw_text',
            'extracted_json',
            'confidence_score',
            'error_message',
            'created_at',
            'updated_at',
        )

