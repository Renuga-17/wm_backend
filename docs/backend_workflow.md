# Backend Workflow

This document illustrates key process workflows executed on the Warehouse Management backend.

## AI-Assisted Inbound Product Placement

1. **Inbound Shipment Arrival**: Staff scans the incoming goods.
2. **Recommendation Request**: The WMS calls `apps.recommendations.services.get_placement_recommendation()`.
3. **AI Evaluation**:
   - Fetches product specs (SKU, weight, temperature sensitivity).
   - Fetches current warehouse layout & occupation status from PostgreSQL.
   - Converts product tags to embeddings and checks Qdrant for affinity with other items in the zone.
   - Calls the **FastAPI AI Service** through `integrations.ai_service_client.py`.
4. **Result Action**:
   - Returns the optimal warehouse bin path to the operator.
   - Generates a movement ticket in `apps.movements`.
