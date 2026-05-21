from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Warehouse Admin'),
        ('MANAGER', 'Warehouse Manager'),
        ('STAFF', 'Warehouse Staff'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    warehouse = models.ForeignKey(
        'warehouses.Warehouse', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='staff_members'
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
