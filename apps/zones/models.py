from django.db import models

class Zone(models.Model):
    # Placeholder model for zones
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Zone #{self.pk}"
