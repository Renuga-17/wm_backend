import uuid
from decimal import Decimal
from django.db import models

class Warehouse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='warehouse_id')
    name = models.CharField(max_length=100)
    location = models.TextField(blank=True, null=True)
    total_area_sqft = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'warehouses'

    def __str__(self):
        return self.name

class WarehouseLayout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='layout_id')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, db_column='warehouse_id', related_name='layouts')
    layout_name = models.CharField(max_length=100)
    cad_file_url = models.TextField(blank=True, null=True)
    width = models.DecimalField(max_digits=10, decimal_places=2)
    height = models.DecimalField(max_digits=10, decimal_places=2)
    depth = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'warehouse_layouts'

    def __str__(self):
        return f"{self.layout_name} - {self.warehouse.name}"

class CADObject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='object_id')
    layout = models.ForeignKey(WarehouseLayout, on_delete=models.CASCADE, db_column='layout_id', related_name='cad_objects')
    object_type = models.CharField(max_length=50)
    detected_label = models.CharField(max_length=100)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4)
    x = models.DecimalField(max_digits=10, decimal_places=4)
    y = models.DecimalField(max_digits=10, decimal_places=4)
    z = models.DecimalField(max_digits=10, decimal_places=4)
    width = models.DecimalField(max_digits=10, decimal_places=4)
    height = models.DecimalField(max_digits=10, decimal_places=4)
    depth = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        db_table = 'cad_objects'

    def __str__(self):
        return f"{self.detected_label} ({self.object_type})"

class MLExtraction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='extraction_id')
    object = models.ForeignKey(CADObject, on_delete=models.CASCADE, db_column='object_id', related_name='ml_extractions')
    extracted_data = models.JSONField()
    model_version = models.CharField(max_length=50)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ml_extractions'

    def __str__(self):
        return f"Extraction {self.id} (Model: {self.model_version})"


class Rack(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='rack_id')
    zone = models.ForeignKey('warehouse.Zone', on_delete=models.CASCADE, db_column='zone_id', related_name='racks')
    aisle = models.ForeignKey('warehouse.Aisle', on_delete=models.SET_NULL, null=True, blank=True, db_column='aisle_id', related_name='racks')
    rack_code = models.CharField(max_length=50, unique=True)
    max_weight = models.DecimalField(max_digits=10, decimal_places=2)
    x = models.DecimalField(max_digits=10, decimal_places=4)
    y = models.DecimalField(max_digits=10, decimal_places=4)
    z = models.DecimalField(max_digits=10, decimal_places=4)
    width = models.DecimalField(max_digits=10, decimal_places=4)
    height = models.DecimalField(max_digits=10, decimal_places=4)
    depth = models.DecimalField(max_digits=10, decimal_places=4)
    rotation_angle = models.DecimalField(max_digits=8, decimal_places=4)

    class Meta:
        db_table = 'racks'

    def __str__(self):
        return self.rack_code


class SpatialEntity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='entity_id')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, db_column='warehouse_id', related_name='spatial_entities')
    entity_name = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50)  # OBSTACLE, DOCK, PATHWAY, etc.
    x = models.DecimalField(max_digits=10, decimal_places=4)
    y = models.DecimalField(max_digits=10, decimal_places=4)
    z = models.DecimalField(max_digits=10, decimal_places=4)
    width = models.DecimalField(max_digits=10, decimal_places=4)
    height = models.DecimalField(max_digits=10, decimal_places=4)
    depth = models.DecimalField(max_digits=10, decimal_places=4)
    rotation_angle = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'spatial_entities'

    def __str__(self):
        return f"{self.entity_name} ({self.entity_type})"


class NavigationNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='node_id')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, db_column='warehouse_id', related_name='navigation_nodes')
    node_name = models.CharField(max_length=100)
    node_type = models.CharField(max_length=50)  # PICK_POINT, INTERSECTION, DOCK, etc.
    x = models.DecimalField(max_digits=10, decimal_places=4)
    y = models.DecimalField(max_digits=10, decimal_places=4)
    z = models.DecimalField(max_digits=10, decimal_places=4)
    connections = models.JSONField(default=list, blank=True)  # List of connected node_ids and edge weights

    class Meta:
        db_table = 'navigation_graph'

    def __str__(self):
        return f"{self.node_name} ({self.node_type})"


class WarehousePath(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='path_id')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, db_column='warehouse_id', related_name='paths')
    path_name = models.CharField(max_length=100)
    start_x = models.DecimalField(max_digits=10, decimal_places=4)
    start_y = models.DecimalField(max_digits=10, decimal_places=4)
    start_z = models.DecimalField(max_digits=10, decimal_places=4)
    end_x = models.DecimalField(max_digits=10, decimal_places=4)
    end_y = models.DecimalField(max_digits=10, decimal_places=4)
    end_z = models.DecimalField(max_digits=10, decimal_places=4)
    width = models.DecimalField(max_digits=10, decimal_places=4)
    is_two_way = models.BooleanField(default=True)

    class Meta:
        db_table = 'warehouse_paths'

    def __str__(self):
        return self.path_name


class RackCoordinate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='coordinate_id')
    rack = models.ForeignKey('warehouse.Rack', on_delete=models.CASCADE, db_column='rack_id', related_name='coordinates')
    access_point_x = models.DecimalField(max_digits=10, decimal_places=4)
    access_point_y = models.DecimalField(max_digits=10, decimal_places=4)
    access_point_z = models.DecimalField(max_digits=10, decimal_places=4)
    side = models.CharField(max_length=50)

    class Meta:
        db_table = 'rack_coordinates'

    def __str__(self):
        return f"Access to {self.rack.rack_code} - {self.side}"


class NavigationEdge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='edge_id')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, db_column='warehouse_id', related_name='navigation_edges')
    from_node = models.ForeignKey(NavigationNode, on_delete=models.CASCADE, related_name='outgoing_edges', db_column='from_node_id')
    to_node = models.ForeignKey(NavigationNode, on_delete=models.CASCADE, related_name='incoming_edges', db_column='to_node_id')
    edge_weight = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)
    congestion_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    is_blocked = models.BooleanField(default=False)
    travel_time = models.DecimalField(max_digits=10, decimal_places=4, default=0.0)
    dynamic_cost = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)

    class Meta:
        db_table = 'navigation_edges'
        unique_together = ('from_node', 'to_node')

    def save(self, *args, **kwargs):
        if self.is_blocked:
            self.dynamic_cost = Decimal('999999.9999')
        else:
            cost_val = float(self.edge_weight) * (1.0 + float(self.congestion_score)) + 0.1 * float(self.travel_time)
            self.dynamic_cost = Decimal(f"{cost_val:.4f}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.from_node.node_name} -> {self.to_node.node_name} (cost: {self.dynamic_cost})"




