from django.db import models

class Product(models.Model):
    # Placeholder model for products
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Product #{self.pk}"
