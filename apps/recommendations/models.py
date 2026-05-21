from django.db import models

class Recommendation(models.Model):
    # Placeholder model for recommendations
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recommendation #{self.pk}"
