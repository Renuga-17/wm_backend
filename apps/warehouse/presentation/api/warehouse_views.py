from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.warehouse.infrastructure.persistence.models import (
    Warehouse, Rack, SpatialEntity, NavigationNode, WarehousePath, 
    RackCoordinate, Zone, Shelf, Bin
)
from .serializers import (
    WarehouseSerializer, RackSerializer, SpatialEntitySerializer,
    NavigationNodeSerializer, WarehousePathSerializer, RackCoordinateSerializer
)
from common.permissions import ReadOnlyOrAuthenticated


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by('id')
    serializer_class = WarehouseSerializer
    permission_classes = [ReadOnlyOrAuthenticated]

    @action(detail=True, methods=['get'], url_path='cad-layout')
    def cad_layout(self, request, pk=None):
        warehouse = self.get_object()

        # Query zones, racks, shelves, and bins with prefetching to avoid N+1 queries
        zones = Zone.objects.filter(warehouse=warehouse).select_related('zone_group').order_by('id')
        racks = Rack.objects.filter(zone__warehouse=warehouse).select_related('zone').order_by('id')
        shelves = Shelf.objects.filter(rack__zone__warehouse=warehouse).select_related('rack').order_by('id')
        bins = Bin.objects.filter(shelf__rack__zone__warehouse=warehouse).select_related('shelf', 'shelf__rack').order_by('id')

        # Calculate a dynamic bounding box from child components
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        has_elements = False

        for z in zones:
            if z.x is not None:
                min_x = min(min_x, float(z.x))
                max_x = max(max_x, float(z.x) + float(z.width or 0))
            if z.y is not None:
                min_y = min(min_y, float(z.y))
                max_y = max(max_y, float(z.y) + float(z.depth or 0))
            if z.z is not None:
                min_z = min(min_z, float(z.z))
                max_z = max(max_z, float(z.z) + float(z.height or 0))
            has_elements = True

        for r in racks:
            if r.x is not None:
                # Rack r.x/y represents center point
                r_w = float(r.width or 0)
                r_d = float(r.depth or 0)
                min_x = min(min_x, float(r.x) - r_w / 2.0)
                max_x = max(max_x, float(r.x) + r_w / 2.0)
                min_y = min(min_y, float(r.y) - r_d / 2.0)
                max_y = max(max_y, float(r.y) + r_d / 2.0)
            if r.z is not None:
                # Rack r.z is base point
                min_z = min(min_z, float(r.z))
                max_z = max(max_z, float(r.z) + float(r.height or 0))
            has_elements = True

        bounding_box = None
        if has_elements and min_x != float('inf'):
            bounding_box = {
                "min_x": round(min_x, 2),
                "min_y": round(min_y, 2),
                "min_z": round(min_z, 2),
                "max_x": round(max_x, 2),
                "max_y": round(max_y, 2),
                "max_z": round(max_z, 2),
                "width": round(max_x - min_x, 2),
                "depth": round(max_y - min_y, 2),
                "height": round(max_z - min_z, 2)
            }

        def to_float(val):
            return float(val) if val is not None else None

        def to_meters(val):
            if val is None:
                return None
            f_val = float(val)
            # If the value is > 5.0, it is stored in centimeters in the DB; convert to meters.
            if f_val > 5.0:
                return round(f_val / 100.0, 4)
            return round(f_val, 4)

        payload = {
            "warehouse": {
                "id": str(warehouse.id),
                "name": warehouse.name,
                "x_coordinate": to_float(warehouse.x_coordinate),
                "y_coordinate": to_float(warehouse.y_coordinate),
                "z_coordinate": to_float(warehouse.z_coordinate),
                "width": to_float(warehouse.width),
                "depth": to_float(warehouse.depth),
                "height": to_float(warehouse.height),
                "rotation": to_float(warehouse.rotation),
                "calculated_bounding_box": bounding_box,
            },
            "zones": [
                {
                    "id": str(z.id),
                    "name": z.zone_name,
                    "zone_group_id": str(z.zone_group.id) if z.zone_group else None,
                    "x_coordinate": to_float(z.x),
                    "y_coordinate": to_float(z.y),
                    "z_coordinate": to_float(z.z),
                    "width": to_float(z.width),
                    "depth": to_float(z.depth),
                    "height": to_float(z.height),
                    "rotation": to_float(z.rotation),
                }
                for z in zones
            ],
            "racks": [
                {
                    "id": str(r.id),
                    "name": r.rack_code,
                    "zone_id": str(r.zone.id) if r.zone else None,
                    "x_coordinate": to_float(r.x),
                    "y_coordinate": to_float(r.y),
                    "z_coordinate": to_float(r.z),
                    "width": to_float(r.width),
                    "depth": to_float(r.depth),
                    "height": to_float(r.height),
                    "rotation": to_float(r.rotation_angle),
                }
                for r in racks
            ],
            "shelves": [
                {
                    "id": str(s.id),
                    "rack_id": str(s.rack.id) if s.rack else None,
                    "level": s.shelf_number,
                    "x_coordinate": to_float(s.x_coordinate),
                    "y_coordinate": to_float(s.y_coordinate),
                    "z_coordinate": to_float(s.z_coordinate),
                    "width": to_float(s.width),
                    "depth": to_float(s.depth),
                    "height": to_float(s.height),
                }
                for s in shelves
            ],
            "bins": [
                {
                    "id": str(b.id),
                    "code": b.bin_code,
                    "shelf_id": str(b.shelf.id) if b.shelf else None,
                    "rack_id": str(b.shelf.rack.id) if b.shelf and b.shelf.rack else None,
                    "x_coordinate": to_float(b.x_coordinate),
                    "y_coordinate": to_float(b.y_coordinate),
                    "z_coordinate": to_float(b.z_coordinate),
                    "width": to_meters(b.width),
                    "depth": to_meters(b.length),  # Map Bin.length → depth
                    "height": to_meters(b.height),
                    "rotation": to_float(b.rotation),
                    "status": "occupied" if b.is_occupied else "available",
                }
                for b in bins
            ],
        }

        return Response(payload, status=status.HTTP_200_OK)


class RackViewSet(viewsets.ModelViewSet):
    queryset = Rack.objects.all().order_by('id')
    serializer_class = RackSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class SpatialEntityViewSet(viewsets.ModelViewSet):
    queryset = SpatialEntity.objects.all().order_by('id')
    serializer_class = SpatialEntitySerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class NavigationNodeViewSet(viewsets.ModelViewSet):
    queryset = NavigationNode.objects.all().order_by('id')
    serializer_class = NavigationNodeSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class WarehousePathViewSet(viewsets.ModelViewSet):
    queryset = WarehousePath.objects.all().order_by('id')
    serializer_class = WarehousePathSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class RackCoordinateViewSet(viewsets.ModelViewSet):
    queryset = RackCoordinate.objects.all().order_by('id')
    serializer_class = RackCoordinateSerializer
    permission_classes = [ReadOnlyOrAuthenticated]
