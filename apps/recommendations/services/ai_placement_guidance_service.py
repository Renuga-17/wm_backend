import logging
from integrations.ai_service_client import AIServiceClient

logger = logging.getLogger(__name__)

class AIPlacementGuidanceService:
    def __init__(self):
        self.ai_client = AIServiceClient()

    def generate_instructions(self, product_dim, selected_orientation, placement_3d, bin_obj) -> str:
        try:
            strategy = placement_3d.placement_strategy
            label_dir = placement_3d.label_direction
            util = float(placement_3d.utilization_percentage)
            
            # Strategy Mapping
            strategy_desc = "horizontally"
            if strategy == 'STACKED':
                strategy_desc = "stacked on top of existing inventory"
            elif strategy == 'CORNER_ALIGN':
                strategy_desc = "aligned into the back corner"
                
            # Label Mapping
            label_desc = "facing outward"
            if label_dir == 'TOP':
                label_desc = "facing upward"
            elif label_dir == 'SIDE':
                label_desc = "facing the side"

            steps = [
                f"Place the product {strategy_desc}.",
                f"Align the product to dimensions: {selected_orientation}.",
                f"Keep the label {label_desc}.",
                f"This orientation provides optimal space utilization of {util:.1f}%."
            ]
            return "\n\n".join(steps)
        except Exception as e:
            logger.warning("Local placement template failed, falling back to Gemini: %s", str(e))
            try:
                # Compile a context dictionary for Gemini
                context = {
                    "product_dimensions": f"{product_dim.length}x{product_dim.width}x{product_dim.height}" if product_dim else "unknown",
                    "selected_orientation": selected_orientation,
                    "strategy": placement_3d.placement_strategy if placement_3d else "unknown",
                    "label_direction": placement_3d.label_direction if placement_3d else "unknown",
                    "utilization": float(placement_3d.utilization_percentage) if placement_3d else 0.0,
                    "bin_dimensions": f"{bin_obj.length}x{bin_obj.width}x{bin_obj.height}" if bin_obj else "unknown"
                }
                ai_res = self.ai_client.generate_placement_guidance(context)
                return ai_res.get("instructions", "Fallback: Orient product to fit in bin.")
            except Exception as ex:
                logger.error("Gemini placement fallback failed: %s", str(ex))
                return "Fallback: Orient the product horizontally for best placement."
