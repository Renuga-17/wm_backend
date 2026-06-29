import os
import sys
import django
import time
import tracemalloc

sys.path.append(r"c:\TYN\wm_backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection, reset_queries
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.inbound.infrastructure.persistence.models import OCRDocument

User = get_user_model()
user = User.objects.filter(role='STAFF').first()
if not user:
    user = User.objects.create_user(
        username='benchmark_staff_user',
        password='testpassword123',
        email='bench_staff@warehouse.com',
        role='STAFF'
    )

# Ensure some dummy OCRDocuments exist for database list and retrieval metrics
if OCRDocument.objects.count() < 10:
    for i in range(10):
        OCRDocument.objects.create(
            file_name=f"test_invoice_{i}.png",
            file_path=f"ocr_documents/test_invoice_{i}.png",
            document_type="invoice",
            document_hash=f"hash_val_abc_123_{i}",
            confidence_score=0.90 if i % 2 == 0 else 0.70,
            processing_status=OCRDocument.ProcessingStatus.COMPLETED if i % 2 == 0 else OCRDocument.ProcessingStatus.REVIEW_REQUIRED,
            raw_text="DUMMY EXTRACTED TEXT FROM OCR",
        )

doc = OCRDocument.objects.first()

client = APIClient()
client.force_authenticate(user=user)

# 1. Warm up
client.get('/api/ocr/documents/')

# Start tracking memory
tracemalloc.start()
reset_queries()

t0 = time.perf_counter()
mem_start, _ = tracemalloc.get_traced_memory()

# Run the target queries/endpoints
res_list = client.get('/api/ocr/documents/')
res_queue = client.get('/api/ocr/documents/review-queue/')
res_detail = client.get(f'/api/ocr/documents/{doc.id}/')

t1 = time.perf_counter()
_, mem_peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

queries_count = len(connection.queries)

print("==================================================")
print("OCR DOCUMENT APIs PERFORMANCE BENCHMARK")
print("==================================================")
print(f"List response status: {res_list.status_code}, data length: {len(res_list.data)}")
print(f"Queue response status: {res_queue.status_code}, data length: {len(res_queue.data)}")
print(f"Detail response status: {res_detail.status_code}")
print(f"Total time taken: {t1 - t0:.6f} seconds")
print(f"Total SQL queries executed: {queries_count}")
print(f"Peak memory during execution: {mem_peak / 1024:.2f} KB")
print("==================================================")
for idx, q in enumerate(connection.queries, start=1):
    print(f"Query #{idx} in {q['time']}s: {q['sql']}\n")
