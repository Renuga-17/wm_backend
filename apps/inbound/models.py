from django.db import models

class Inbound(models.Model):
    # Placeholder model for inbound
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Inbound #{self.pk}"
