from django.db import models

class Bin(models.Model):
    # Placeholder model for bins
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bin #{self.pk}"
