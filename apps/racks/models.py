from django.db import models

class Rack(models.Model):
    # Placeholder model for racks
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rack #{self.pk}"
