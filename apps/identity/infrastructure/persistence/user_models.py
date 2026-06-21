import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

class User(AbstractUser):
    objects = UserManager()

    ROLE_CHOICES = (
        ('ADMIN', 'Warehouse Admin'),
        ('MANAGER', 'Warehouse Manager'),
        ('STAFF', 'Warehouse Staff'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_column='user_id')  # type: ignore
    full_name = models.CharField(max_length=100, db_column='full_name', blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='STAFF', db_column='role')
    warehouse = models.ForeignKey(
        'warehouse.Warehouse', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='staff_members',
        db_column='warehouse_id'
    )

    class Meta(AbstractUser.Meta):
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.role})"

