from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.bins.models import Bin

channel_layer = get_channel_layer()

@receiver(post_save, sender=Bin)
def bin_saved(sender, instance, created, **kwargs):
    if channel_layer:
        payload = {
            "type": "occupancy_message",
            "message": {
                "rack_id": str(instance.shelf.rack.id) if instance.shelf and instance.shelf.rack else None,
                "bin_id": str(instance.id),
                "is_occupied": instance.is_occupied,
                "current_capacity": str(instance.current_capacity)
            }
        }
        try:
            async_to_sync(channel_layer.group_send)('occupancy_updates', payload)
        except Exception:
            pass

