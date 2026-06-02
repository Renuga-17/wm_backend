import sys
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.warehouses.models import CADObject, NavigationNode

class Command(BaseCommand):
    help = "Generate NavigationNode records from CADObject data"

    def handle(self, *args, **options):
        total = CADObject.objects.count()
        created = 0
        skipped = 0

        # Simple mapping from label prefixes to node_type
        def map_node_type(label):
            lname = label.lower()
            if "dock" in lname:
                return "DOCK"
            if "packing" in lname:
                return "PACKING"
            if "rack" in lname:
                return "RACK"
            return None

        with transaction.atomic():
            for obj in CADObject.objects.select_related('layout__warehouse'):
                node_type = map_node_type(obj.detected_label)
                if not node_type:
                    skipped += 1
                    continue
                warehouse = obj.layout.warehouse
                node, created_flag = NavigationNode.objects.get_or_create(
                    warehouse=warehouse,
                    node_name=obj.detected_label,
                    defaults={
                        "node_type": node_type,
                        "x": obj.x,
                        "y": obj.y,
                        "z": obj.z,
                    },
                )
                if created_flag:
                    created += 1
                else:
                    # Ensure fields are up‑to‑date if they differ
                    needs_save = False
                    if node.node_type != node_type:
                        node.node_type = node_type
                        needs_save = True
                    if node.x != obj.x:
                        node.x = obj.x
                        needs_save = True
                    if node.y != obj.y:
                        node.y = obj.y
                        needs_save = True
                    if node.z != obj.z:
                        node.z = obj.z
                        needs_save = True
                    if needs_save:
                        node.save()
                    skipped += 1

        self.stdout.write(
            f"CADObjects processed: {total} | Nodes created: {created} | Nodes skipped/updated: {skipped}"
        )
