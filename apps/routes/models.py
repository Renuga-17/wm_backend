import uuid
from django.db import models
from apps.warehouses.models import Warehouse

class OptimizedRoute(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='route_id')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='optimized_routes', null=True)
    start_location = models.CharField(max_length=100)
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_time = models.IntegerField(help_text="Estimated time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'optimized_routes'

    def __str__(self):
        return f"Route {self.id} from {self.start_location}"

class RouteSegment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='segment_id')
    route = models.ForeignKey(OptimizedRoute, on_delete=models.CASCADE, related_name='segments')
    segment_order = models.IntegerField()
    x = models.DecimalField(max_digits=10, decimal_places=4)
    y = models.DecimalField(max_digits=10, decimal_places=4)
    z = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    class Meta:
        db_table = 'route_segments'
        ordering = ['segment_order']

    def __str__(self):
        return f"Segment {self.segment_order} for {self.route.id}"

class RouteHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='history_id')
    route = models.ForeignKey(OptimizedRoute, on_delete=models.CASCADE, related_name='history')
    executed_by = models.CharField(max_length=100, blank=True, null=True)  # could be user or robot id
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='PENDING')

    class Meta:
        db_table = 'route_history'

    def __str__(self):
        return f"History for {self.route.id} - {self.status}"

class StorageLocationNodeMap(models.Model):
    """Map a storage entity (Bin, Shelf, Rack, or Zone) to a NavigationNode.
    Exactly one of the storage foreign‑key fields must be non‑null.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='map_id')
    warehouse = models.ForeignKey(
        'warehouses.Warehouse',
        on_delete=models.CASCADE,
        db_column='warehouse_id',
        related_name='location_node_maps',
    )
    # Nullable one‑to‑one links – only one may be set per row
    bin = models.OneToOneField(
        'bins.Bin',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='bin_id',
        related_name='node_map',
    )
    shelf = models.OneToOneField(
        'bins.Shelf',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='shelf_id',
        related_name='node_map',
    )
    rack = models.OneToOneField(
        'warehouses.Rack',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='rack_id',
        related_name='node_map',
    )
    zone = models.OneToOneField(
        'zones.Zone',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='zone_id',
        related_name='node_map',
    )
    navigation_node = models.ForeignKey(
        'warehouses.NavigationNode',
        on_delete=models.CASCADE,
        db_column='navigation_node_id',
        related_name='location_maps',
    )

    class Meta:
        db_table = 'storage_location_node_map'
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(bin__isnull=False, shelf__isnull=True, rack__isnull=True, zone__isnull=True) |
                    models.Q(bin__isnull=True, shelf__isnull=False, rack__isnull=True, zone__isnull=True) |
                    models.Q(bin__isnull=True, shelf__isnull=True, rack__isnull=False, zone__isnull=True) |
                    models.Q(bin__isnull=True, shelf__isnull=True, rack__isnull=True, zone__isnull=False)
                ),
                name='exactly_one_storage_fk',
            )
        ]

    def __str__(self):
        parts = []
        if self.bin:
            parts.append(f"Bin {self.bin.bin_code}")
        if self.shelf:
            parts.append(f"Shelf {self.shelf.shelf_number}")
        if self.rack:
            parts.append(f"Rack {self.rack.rack_code}")
        if self.zone:
            parts.append(f"Zone {self.zone.zone_name}")
        return f"{' | '.join(parts)} → {self.navigation_node.node_name}"
