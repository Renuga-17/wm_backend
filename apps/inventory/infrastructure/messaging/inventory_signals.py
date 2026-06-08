from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Inventory

channel_layer = get_channel_layer()

@receiver(post_save, sender=Inventory)
def inventory_item_saved(sender, instance, created, **kwargs):
    if channel_layer:
        action = "created" if created else "updated"
        payload = {
            "type": "inventory_message",
            "message": {
                "action": action,
                "inventory_id": str(instance.id),
                "product_id": str(instance.product.id) if instance.product else None,
                "total_quantity": str(instance.total_quantity)
            }
        }
        try:
            async_to_sync(channel_layer.group_send)('inventory_updates', payload)
        except Exception:
            pass

@receiver(post_delete, sender=Inventory)
def inventory_item_deleted(sender, instance, **kwargs):
    if channel_layer:
        payload = {
            "type": "inventory_message",
            "message": {
                "action": "deleted",
                "inventory_id": str(instance.id)
            }
        }
        try:
            async_to_sync(channel_layer.group_send)('inventory_updates', payload)
        except Exception:
            pass

