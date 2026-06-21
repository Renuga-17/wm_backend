import logging
from integrations.ai_service_client import AIServiceClient

logger = logging.getLogger(__name__)

class AINavigationGuidanceService:
    def __init__(self):
        self.ai_client = AIServiceClient()

    def generate_instructions(self, zone, rack, shelf, bin_obj, route_data) -> str:
        try:
            start_loc = route_data.get("start_location", "DOCK_A")
            distance = route_data.get("distance", 0.0)
            
            steps = [
                f"Walk straight from {start_loc}.",
                f"Continue for {distance:.1f} meters to {zone.zone_name}.",
                f"Proceed to Rack {rack.rack_code}.",
                f"Locate Shelf {shelf.shelf_number}.",
                f"Place the product in Bin {bin_obj.bin_code}."
            ]
            return "\n\n".join(steps)
        except Exception as e:
            logger.warning("Local navigation template failed, falling back to Gemini: %s", str(e))
            try:
                ai_res = self.ai_client.generate_navigation_guidance(route_data)
                return ai_res.get("instructions", "Fallback: Follow route coordinates to target bin.")
            except Exception as ex:
                logger.error("Gemini navigation fallback failed: %s", str(ex))
                return "Fallback: Proceed along the calculated coordinates path."
