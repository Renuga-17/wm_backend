import uuid

def generate_unique_code(prefix="WMS"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
