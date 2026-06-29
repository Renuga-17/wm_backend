from decimal import Decimal
from django.db import transaction
from apps.warehouse.models import Rack, Shelf, Bin

class TopologyGenerationService:
    @staticmethod
    def generate_rack_topology(rack: Rack, shelves_per_rack: int = 4, bins_per_shelf: int = 5):
        """
        Generates shelves and bins grid for a specific rack.
        """
        # Calculate heights and coordinate offsets
        rack_height = float(rack.height)
        rack_width = float(rack.width)
        rack_depth = float(rack.depth)

        shelf_height = rack_height / shelves_per_rack
        bin_width = rack_width / bins_per_shelf
        bin_depth = rack_depth

        shelf_max_weight = Decimal(str(float(rack.max_weight) / shelves_per_rack))

        created_shelves = []
        created_bins = []

        with transaction.atomic():
            # Delete obsolete shelves (e.g. if count decreased)
            Shelf.objects.filter(rack=rack, shelf_number__gt=shelves_per_rack).delete()

            for i in range(1, shelves_per_rack + 1):
                height_from_ground = (i - 1) * shelf_height
                shelf_z = float(rack.z) + height_from_ground if rack.z is not None else height_from_ground
                
                # Check if shelf already exists
                shelf, shelf_created = Shelf.objects.get_or_create(
                    rack=rack,
                    shelf_number=i,
                    defaults={
                        'max_weight': shelf_max_weight,
                        'height_from_ground': Decimal(str(height_from_ground)),
                        'x_coordinate': rack.x,
                        'y_coordinate': rack.y,
                        'z_coordinate': Decimal(str(shelf_z)),
                        'width': rack.width,
                        'depth': rack.depth,
                        'height': Decimal(str(shelf_height))
                    }
                )

                if not shelf_created:
                    # Update fields, but preserve manually entered non-null coordinates/dimensions
                    if shelf.x_coordinate is None:
                        shelf.x_coordinate = rack.x
                    if shelf.y_coordinate is None:
                        shelf.y_coordinate = rack.y
                    if shelf.z_coordinate is None:
                        shelf.z_coordinate = Decimal(str(shelf_z))
                    if shelf.width is None:
                        shelf.width = rack.width
                    if shelf.depth is None:
                        shelf.depth = rack.depth
                    if shelf.height is None:
                        shelf.height = Decimal(str(shelf_height))
                    shelf.max_weight = shelf_max_weight
                    shelf.height_from_ground = Decimal(str(height_from_ground))
                    shelf.save()

                created_shelves.append(shelf)

                left_edge_x = float(rack.x) - (rack_width / 2.0) if rack.x is not None else 0.0

                # Obsolete bins on this shelf: delete if not in the valid grid range
                valid_bin_codes = [f"{rack.rack_code}-S{i}-B{j:02d}" for j in range(1, bins_per_shelf + 1)]
                Bin.objects.filter(shelf=shelf).exclude(bin_code__in=valid_bin_codes).delete()

                for j in range(1, bins_per_shelf + 1):
                    # Calculate center coordinates of each bin
                    bin_x = left_edge_x + (j - 0.5) * bin_width
                    bin_y = float(rack.y) if rack.y is not None else 0.0
                    bin_z = (float(rack.z) if rack.z is not None else 0.0) + height_from_ground

                    # Volume is length * width * height
                    bin_volume = bin_width * bin_depth * shelf_height

                    bin_obj, bin_created = Bin.objects.get_or_create(
                        shelf=shelf,
                        bin_code=f"{rack.rack_code}-S{i}-B{j:02d}",
                        defaults={
                            'max_capacity': Decimal(str(bin_volume)),
                            'current_capacity': Decimal('0.00'),
                            'length': Decimal(str(bin_width)),
                            'width': Decimal(str(bin_depth)),
                            'height': Decimal(str(shelf_height)),
                            'is_occupied': False,
                            'x_coordinate': Decimal(str(bin_x)),
                            'y_coordinate': Decimal(str(bin_y)),
                            'z_coordinate': Decimal(str(bin_z)),
                            'rotation': rack.rotation_angle
                        }
                    )

                    if not bin_created:
                        # Update dimensions/capacity, but preserve manually entered non-null coordinates/rotation
                        if bin_obj.x_coordinate is None:
                            bin_obj.x_coordinate = Decimal(str(bin_x))
                        if bin_obj.y_coordinate is None:
                            bin_obj.y_coordinate = Decimal(str(bin_y))
                        if bin_obj.z_coordinate is None:
                            bin_obj.z_coordinate = Decimal(str(bin_z))
                        if bin_obj.rotation is None:
                            bin_obj.rotation = rack.rotation_angle
                        bin_obj.max_capacity = Decimal(str(bin_volume))
                        bin_obj.length = Decimal(str(bin_width))
                        bin_obj.width = Decimal(str(bin_depth))
                        bin_obj.height = Decimal(str(shelf_height))
                        bin_obj.save()

                    created_bins.append(bin_obj)

        return created_shelves, created_bins
