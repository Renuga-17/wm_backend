from django.db import models

class Movement(models.Model):
    # Placeholder model for movements
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Movement #{self.pk}"
