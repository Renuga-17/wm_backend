import uuid
from typing import List, Dict

from ...models import (
    StorageLocationNodeMap,
    Bin,
    Shelf,
    Rack,
    Zone,
)

from .pathfinding import PathfindingService


class RouteOptimizer:
    """Service for computing routes within a warehouse.

    The service resolves a start location (e.g., a receiving gate) and a target
    storage location (bin, shelf, rack, or zone) to their corresponding
    ``NavigationNode`` objects, then finds the shortest path using the existing
    ``PathfindingService`` implementation.
    """

    @staticmethod
    def _resolve_target_node(warehouse_id: uuid.UUID, location_code: str):
        """Resolve a storage identifier (bin code, shelf number, rack code, etc.)
        to a ``NavigationNode`` via the ``StorageLocationNodeMap``.
        """
        # Try Bin first (most specific)
        try:
            bin_obj = Bin.objects.select_related('shelf__rack__zone').get(bin_code=location_code)
        except Bin.DoesNotExist:
            bin_obj = None
        if bin_obj:
            mapping = StorageLocationNodeMap.objects.filter(bin=bin_obj).first()
            if mapping:
                return mapping.navigation_node
        # Try Shelf code (constructed as "{rack_code}_S{shelf_number}")
        # Shelf does not have a unique code, so we attempt a simple heuristic
        # of matching the provided string against ``shelf_number`` when the
        # string is numeric.
        if location_code.isdigit():
            try:
                shelf_obj = Shelf.objects.get(shelf_number=int(location_code))
                mapping = StorageLocationNodeMap.objects.filter(shelf=shelf_obj).first()
                if mapping:
                    return mapping.navigation_node
            except Shelf.DoesNotExist:
                pass
        # Try Rack code directly
        try:
            rack_obj = Rack.objects.get(rack_code=location_code)
            mapping = StorageLocationNodeMap.objects.filter(rack=rack_obj).first()
            if mapping:
                return mapping.navigation_node
        except Rack.DoesNotExist:
            pass
        # Finally try Zone name
        try:
            zone_obj = Zone.objects.get(zone_name=location_code)
            mapping = StorageLocationNodeMap.objects.filter(zone=zone_obj).first()
            if mapping:
                return mapping.navigation_node
        except Zone.DoesNotExist:
            pass
        raise ValueError(f"Could not resolve storage location '{location_code}' to a navigation node.")

    @staticmethod
    def compute_route(
        warehouse_id: uuid.UUID,
        start_location: str,
        target_location: str,
    ) -> Dict:
        """Compute the shortest route from ``start_location`` to ``target_location``.

        Parameters
        ----------
        warehouse_id: UUID of the warehouse.
        start_location: Name of the start node (e.g., "Receiving Gate").
        target_location: Identifier of the destination storage location (bin code,
                         rack code, etc.).

        Returns
        -------
        dict
            ``{"path": [...], "distance": <float>}`` where each element in the
            ``path`` list contains ``node``, ``x``, ``y``, and ``z`` ready for
            Three.js visualisation.
        """
        # Resolve start node using existing pathfinding logic
        start_node = PathfindingService.resolve_location_to_node(warehouse_id, start_location)
        # Resolve target node via mapping model
        target_node = RouteOptimizer._resolve_target_node(warehouse_id, target_location)

        distance, node_path = PathfindingService.a_star_search(warehouse_id, start_node, target_node)
        if distance == float("inf"):
            raise ValueError("No viable route found between the specified points.")

        path_output: List[Dict] = []
        for node in node_path:
            path_output.append(
                {
                    "node": node.node_name,
                    "x": float(node.x),
                    "y": float(node.y),
                    "z": float(node.z),
                }
            )
        return {"path": path_output, "distance": float(distance)}
