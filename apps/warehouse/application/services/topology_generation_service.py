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
            # Clear any existing shelf/bin configurations for clean re-generation
            Shelf.objects.filter(rack=rack).delete()

            for i in range(1, shelves_per_rack + 1):
                height_from_ground = (i - 1) * shelf_height
                shelf = Shelf.objects.create(
                    rack=rack,
                    shelf_number=i,
                    max_weight=shelf_max_weight,
                    height_from_ground=Decimal(str(height_from_ground))
                )
                created_shelves.append(shelf)

                left_edge_x = float(rack.x) - (rack_width / 2.0)

                for j in range(1, bins_per_shelf + 1):
                    # Calculate center coordinates of each bin
                    bin_x = left_edge_x + (j - 0.5) * bin_width
                    bin_y = float(rack.y)
                    bin_z = float(rack.z) + height_from_ground

                    # Volume is length * width * height
                    bin_volume = bin_width * bin_depth * shelf_height

                    bin_obj = Bin.objects.create(
                        shelf=shelf,
                        bin_code=f"{rack.rack_code}-S{i}-B{j:02d}",
                        max_capacity=Decimal(str(bin_volume)),
                        current_capacity=Decimal('0.00'),
                        length=Decimal(str(bin_width)),
                        width=Decimal(str(bin_depth)),
                        height=Decimal(str(shelf_height)),
                        is_occupied=False
                    )
                    created_bins.append(bin_obj)

        return created_shelves, created_bins
