# -*- coding: utf-8 -*-
"""Django management command to populate StorageLocationNodeMap for each Bin.
It links a Bin (through its Shelf and Rack) to the nearest NavigationNode
based on the Rack's x, y, z coordinates. The Warehouse is obtained via
`rack.zone.warehouse`.
Duplicate mappings are skipped to keep the operation idempotent.
"""

from math import sqrt
from django.core.management.base import BaseCommand
from django.db import transaction

from django.apps import apps

Bin = apps.get_model('bins', 'Bin')
StorageLocationNodeMap = apps.get_model('routes', 'StorageLocationNodeMap')
NavigationNode = apps.get_model('warehouses', 'NavigationNode')


class Command(BaseCommand):
    help = "Populate StorageLocationNodeMap for each Bin using the nearest NavigationNode"

    def handle(self, *args, **options):
        total_bins = 0
        created = 0
        skipped = 0
        unmapped = 0

        # Pre‑load all navigation nodes – typically a small set
        navigation_nodes = list(NavigationNode.objects.all())
        if not navigation_nodes:
            self.stdout.write(self.style.ERROR("No NavigationNode records found – aborting."))
            return

        # Iterate over bins, pulling Shelf and Rack in one query to avoid N+1
        bins_qs = Bin.objects.select_related('shelf__rack__zone__warehouse').all()
        for bin_obj in bins_qs:
            total_bins += 1
            shelf = getattr(bin_obj, 'shelf', None)
            rack = getattr(shelf, 'rack', None) if shelf else None
            if not rack:
                unmapped += 1
                continue

            # Find the nearest navigation node using Euclidean distance on rack coordinates
            rack_x, rack_y, rack_z = float(rack.x), float(rack.y), float(rack.z)
            nearest_node = min(
                navigation_nodes,
                key=lambda node: sqrt(
                    (rack_x - float(node.x)) ** 2 +
                    (rack_y - float(node.y)) ** 2 +
                    (rack_z - float(node.z)) ** 2
                ),
            )

            # Idempotent creation using get_or_create to avoid duplicate entries
            mapping, created_flag = StorageLocationNodeMap.objects.get_or_create(
                bin=bin_obj,
                defaults={
                    "warehouse": rack.zone.warehouse,
                    "shelf": None,
                    "rack": None,
                    "zone": None,
                    "navigation_node": nearest_node,
                },
            )
            if created_flag:
                created += 1
            else:
                skipped += 1

        # Summary output
        self.stdout.write(
            f"Processed {total_bins} bins – created {created}, skipped {skipped}, unmapped {unmapped}."
        )
