# -*- coding: utf-8 -*-
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.warehouse.models import Rack, Shelf, Bin


class Command(BaseCommand):
    help = "Backfills coordinates and dimensions for existing Shelf and Bin records from parent Rack records."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Runs the coordinate calculations and prints summary without saving changes to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.NOTICE("=== DRY RUN MODE: No database changes will be saved ==="))

        racks_processed = 0
        racks_skipped = 0
        shelves_updated = 0
        shelves_preserved = 0
        bins_updated = 0
        bins_preserved = 0

        # Run within transaction for DB safety
        try:
            with transaction.atomic():
                racks = Rack.objects.all().order_by('rack_code')

                for rack in racks:
                    # Safeguard: Skip incomplete parent racks
                    if (rack.x is None or rack.y is None or rack.z is None or 
                        rack.width is None or rack.depth is None or rack.height is None):
                        racks_skipped += 1
                        self.stdout.write(self.style.WARNING(
                            f"Skipping Rack '{rack.rack_code}' - coordinate or dimension fields are null."
                        ))
                        continue

                    # Retrieve shelves of the rack
                    shelves = Shelf.objects.filter(rack=rack).order_by('shelf_number')
                    total_shelves = shelves.count()

                    # Safeguard: Skip racks with 0 shelves to avoid division by zero
                    if total_shelves == 0:
                        racks_skipped += 1
                        self.stdout.write(self.style.WARNING(
                            f"Skipping Rack '{rack.rack_code}' - has 0 shelves."
                        ))
                        continue

                    racks_processed += 1

                    rack_height = Decimal(str(rack.height))
                    rack_width = Decimal(str(rack.width))
                    rack_depth = Decimal(str(rack.depth))

                    shelf_height = rack_height / Decimal(str(total_shelves))
                    left_edge_x = Decimal(str(rack.x)) - (rack_width / Decimal('2.0'))

                    for shelf in shelves:
                        i = shelf.shelf_number
                        height_from_ground = Decimal(str(i - 1)) * shelf_height

                        # Calculations based on verified center point for rack.x/y and bottom edge for rack.z
                        shelf_x = rack.x
                        shelf_y = rack.y
                        shelf_z = rack.z + height_from_ground

                        shelf_needs_update = False

                        if shelf.x_coordinate is None:
                            shelf.x_coordinate = shelf_x
                            shelf_needs_update = True
                        if shelf.y_coordinate is None:
                            shelf.y_coordinate = shelf_y
                            shelf_needs_update = True
                        if shelf.z_coordinate is None:
                            shelf.z_coordinate = shelf_z
                            shelf_needs_update = True
                        if shelf.width is None:
                            shelf.width = rack_width
                            shelf_needs_update = True
                        if shelf.depth is None:
                            shelf.depth = rack_depth
                            shelf_needs_update = True
                        if shelf.height is None:
                            shelf.height = shelf_height
                            shelf_needs_update = True

                        if shelf_needs_update:
                            shelves_updated += 1
                            if not dry_run:
                                shelf.save()
                        else:
                            shelves_preserved += 1

                        # Bins on this shelf
                        bins = Bin.objects.filter(shelf=shelf).order_by('bin_code')
                        bins_count = bins.count()

                        if bins_count == 0:
                            continue

                        bin_width = rack_width / Decimal(str(bins_count))
                        bin_depth = rack_depth

                        for idx, bin_obj in enumerate(bins):
                            j = idx + 1
                            bin_x = left_edge_x + (Decimal(str(j)) - Decimal('0.5')) * bin_width
                            bin_y = rack.y
                            bin_z = rack.z + height_from_ground

                            bin_needs_update = False

                            if bin_obj.x_coordinate is None:
                                bin_obj.x_coordinate = bin_x
                                bin_needs_update = True
                            if bin_obj.y_coordinate is None:
                                bin_obj.y_coordinate = bin_y
                                bin_needs_update = True
                            if bin_obj.z_coordinate is None:
                                bin_obj.z_coordinate = bin_z
                                bin_needs_update = True
                            if bin_obj.rotation is None:
                                bin_obj.rotation = rack.rotation_angle
                                bin_needs_update = True

                            # Also fill standard width, length, height fields if currently unset/zero
                            if bin_obj.length is None or bin_obj.length == Decimal('0.00'):
                                bin_obj.length = bin_width
                                bin_needs_update = True
                            if bin_obj.width is None or bin_obj.width == Decimal('0.00'):
                                bin_obj.width = bin_depth
                                bin_needs_update = True
                            if bin_obj.height is None or bin_obj.height == Decimal('0.00'):
                                bin_obj.height = shelf_height
                                bin_needs_update = True

                            if bin_needs_update:
                                bins_updated += 1
                                if not dry_run:
                                    bin_obj.save()
                            else:
                                bins_preserved += 1

                if dry_run:
                    self.stdout.write(self.style.NOTICE("Dry run completed. Rollback active."))
                    raise RuntimeError("Rollback forced in dry run.")

        except RuntimeError as e:
            if "Rollback forced in dry run" not in str(e):
                raise e

        # Output Summary info
        self.stdout.write("\n=== Backfill Summary ===")
        self.stdout.write(f"Racks Processed: {racks_processed}")
        self.stdout.write(f"Racks Skipped:   {racks_skipped}")
        self.stdout.write(f"Shelves Updated: {shelves_updated}")
        self.stdout.write(f"Shelves Preserved: {shelves_preserved}")
        self.stdout.write(f"Bins Updated:    {bins_updated}")
        self.stdout.write(f"Bins Preserved:  {bins_preserved}")
        self.stdout.write("========================\n")
