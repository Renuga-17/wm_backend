from rest_framework import serializers
from .models import OCRDocument


class OCRDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRDocument
        fields = '__all__'
        read_only_fields = (
            'id',
            'extracted_text',
            'structured_data',
            'status',
            'error_message',
            'created_at',
            'updated_at',
        )
