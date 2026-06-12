from django.urls import path
from .rag_query_view import RAGQueryView, RAGHealthView

urlpatterns = [
    path('query/', RAGQueryView.as_view(), name='rag-query'),
    path('rag-health/', RAGHealthView.as_view(), name='rag-health'),
]
