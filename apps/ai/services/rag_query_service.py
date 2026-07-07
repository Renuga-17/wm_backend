import zlib
import json
import logging
from django.db import models
from apps.inbound.infrastructure.persistence.models import OCRDocument
from .rag_client import RAGClient

logger = logging.getLogger(__name__)


def get_user_id_int(user) -> int:
    """Safely converts user ID (which may be a UUID or string) into a 32-bit integer for the RAG service."""
    if not user or not user.is_authenticated:
        return None
    uid = user.id
    if hasattr(uid, 'bytes'):
        return zlib.crc32(uid.bytes)
    try:
        return int(uid)
    except (ValueError, TypeError):
        return zlib.crc32(str(uid).encode())


class RAGQueryService:
    def __init__(self):
        self.client = RAGClient()

    def query_knowledge(self, query: str, user, filters: dict, request_id: str) -> dict:
        logger.info("RAGQueryService: Starting query execution [request_id=%s]", request_id)

        # 1. Normalize Payload
        # Maps backend variables to targets defined in WarehouseRequest
        payload = {
            "ocrDocumentId": None,
            "title": query,
            "description": query,
            "documentType": filters.get("document_type"),
            "priority": "MEDIUM",
            "warehouseId": filters.get("warehouse_id"),
            "sku": filters.get("sku"),
            "productId": filters.get("product_id"),
            "category": filters.get("category"),
            "zone": filters.get("zone"),
            "rack": filters.get("rack"),
            "bin": filters.get("bin"),
            "auditTrail": [],
            "attemptCount": 1,
            "userId": get_user_id_int(user),
        }

        # 2. Heuristic Interceptor for Operational Queries
        operational_answer = self.handle_operational_query(query.lower())
        if operational_answer:
            return {
                "answer": operational_answer,
                "sources": [],
                "filters": {k: v for k, v in filters.items() if v is not None},
            }

        # 3. Call RAGClient
        response_data = self.client.analyze(payload, request_id)

        # 4. Parse Answer
        raw_suggestion = response_data.get("suggestion", "")
        answer = raw_suggestion
        try:
            # If the suggestion is a JSON string wrapped by the RAG model, parse it
            parsed = json.loads(raw_suggestion)
            if isinstance(parsed, dict):
                answer = (
                    parsed.get("analysis_summary")
                    or parsed.get("refined_explanation")
                    or raw_suggestion
                )
        except (json.JSONDecodeError, TypeError):
            # Fallback to the raw string if it is not valid JSON
            pass

        # 5. Resolve and Parse Source Documents
        sources = self.resolve_sources(filters)

        return {
            "answer": answer,
            "sources": sources,
            "filters": {k: v for k, v in filters.items() if v is not None},
        }

    def handle_operational_query(self, query: str) -> str:
        """Dynamic Text-to-SQL router to answer live database queries using Gemini."""
        from django.conf import settings
        from django.db import connection
        from google import genai
        
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return "AI service is not properly configured (Missing API Key)."
            
        client = genai.Client(api_key=api_key)
            
        schema = """
        Table users: user_id, username, full_name, email, role, is_active
        Table zone_groups: id, code, name, description, zone_group_type
        Table zones: id, zone_group_id, zone_name, zone_type
        Table aisles: id, zone_id, code, name
        Table racks: id, zone_id, aisle_id, rack_code
        Table shelves: id, rack_id, shelf_number
        Table bins: id, shelf_id, bin_code, is_occupied, current_capacity
        Table products: id, category_id, sku, product_name, weight, is_fragile
        Table inventory: id, product_id, total_quantity, reserved_quantity
        Table stock_movements: id, product_id, from_bin_id, to_bin_id, quantity, movement_type
        """
        
        # Pass 1: Text to SQL
        prompt_1 = f"""
        You are a Database Agent for a Warehouse Management System.
        Given the following SQLite database schema:
        {schema}
        
        Translate the following user question into a safe, read-only SQL SELECT statement.
        Question: "{query}"
        
        Return ONLY the raw SQL string, nothing else. Do not wrap in markdown blocks.
        """
        
        try:
            resp1 = client.models.generate_content(
                model='gemini-pro-latest',
                contents=prompt_1,
            )
            
            sql_query = resp1.text.strip()
            # Clean markdown if present
            if sql_query.startswith("```sql"): sql_query = sql_query[6:]
            if sql_query.startswith("```"): sql_query = sql_query[3:]
            if sql_query.endswith("```"): sql_query = sql_query[:-3]
            sql_query = sql_query.strip()
            
            # Safety check
            if not sql_query.upper().startswith("SELECT") or "DROP" in sql_query.upper() or "UPDATE" in sql_query.upper() or "DELETE" in sql_query.upper() or "INSERT" in sql_query.upper():
                return "I can only answer questions that read data, not modify it."
                
            logger.info(f"Generated SQL: {sql_query}")
                
            # Execute SQL
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                columns = [col[0] for col in cursor.description]
                results = cursor.fetchmany(50)  # limit to 50 rows
                
                db_results = []
                for row in results:
                    db_results.append(dict(zip(columns, row)))
                    
            if not db_results:
                return "The database does not contain the requested operational data or the result was empty."
                
            # Pass 2: Data to Text
            prompt_2 = f"""
            You are a helpful AI Warehouse Assistant.
            The user asked: "{query}"
            The database returned the following results:
            {db_results}
            
            Write a clear, concise, human-readable answer directly addressing the user's question based on these results.
            """
            
            resp2 = client.models.generate_content(
                model='gemini-pro-latest',
                contents=prompt_2,
            )
            return resp2.text.strip()
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Text-to-SQL Error: {error_msg}")
            if "429" in error_msg or "Quota" in error_msg:
                return "The AI assistant is currently experiencing high traffic and has reached its rate limit. Please try again in about a minute."
            return "An error occurred while querying the live database."

    def resolve_sources(self, filters: dict) -> list:
        sources = []
        qs = OCRDocument.objects.all()

        # Apply filters to find actual source documents
        if filters.get("document_type"):
            qs = qs.filter(document_type=filters["document_type"])

        if filters.get("sku"):
            sku = filters["sku"]
            qs = qs.filter(
                models.Q(raw_text__icontains=sku)
                | models.Q(file_name__icontains=sku)
            )

        # Retrieve top 3 matching documents
        for doc in qs[:3]:
            sources.append({
                "document_id": str(doc.id),
                "document_type": doc.document_type,
                "sku": filters.get("sku") or "",
            })

        return sources
