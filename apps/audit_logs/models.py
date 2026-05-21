from django.db import models

class AuditLog(models.Model):
    # Placeholder model for audit_logs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AuditLog #{self.pk}"
