import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class Tenant(models.Model):
    """Represents a client organization. All data is isolated by tenant."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user model with tenant FK and role."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE,
        related_name='users', null=True, blank=True
    )

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('analyst', 'Analyst'),
        ('viewer', 'Viewer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='analyst')

    EMAIL_FIELD = 'email'

    class Meta:
        ordering = ['email']

    def __str__(self):
        return self.email or self.username
