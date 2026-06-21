from rest_framework import serializers


class RAGQueryInputSerializer(serializers.Serializer):
    query = serializers.CharField(required=True, help_text="The knowledge question to query.")
    sku = serializers.CharField(required=False, allow_null=True, default=None)
    product_id = serializers.CharField(required=False, allow_null=True, default=None)
    category = serializers.CharField(required=False, allow_null=True, default=None)
    warehouse_id = serializers.CharField(required=False, allow_null=True, default=None)
    zone = serializers.CharField(required=False, allow_null=True, default=None)
    rack = serializers.CharField(required=False, allow_null=True, default=None)
    shelf = serializers.CharField(required=False, allow_null=True, default=None)
    bin = serializers.CharField(required=False, allow_null=True, default=None)
    document_type = serializers.CharField(required=False, allow_null=True, default=None)


class SourceDocumentSerializer(serializers.Serializer):
    document_id = serializers.CharField()
    document_type = serializers.CharField()
    sku = serializers.CharField(required=False, allow_blank=True)


class RAGQueryOutputSerializer(serializers.Serializer):
    request_id = serializers.UUIDField(help_text="The tracking ID of the backend request.")
    answer = serializers.CharField(help_text="Synthesized answer from RAG client.")
    sources = SourceDocumentSerializer(many=True, help_text="Sources matched for query.")
    filters = serializers.JSONField(help_text="Filters applied to query.")
