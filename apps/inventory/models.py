from django.db import models

class Inventory(models.Model):
    # Placeholder model for inventory
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Inventory #{self.pk}"
