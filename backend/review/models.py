import uuid
from django.db import models
from core.models import Tenant, User
from ingestion.models import RawRecord, IngestionJob


class NormalizedRecord(models.Model):
    """
    Cleaned, validated emission record ready for analyst review.
    One-to-one with RawRecord to maintain full audit trail.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='normalized_records')
    raw_record = models.OneToOneField(RawRecord, on_delete=models.CASCADE, related_name='normalized')
    ingestion_job = models.ForeignKey(IngestionJob, on_delete=models.CASCADE, related_name='normalized_records')

    SOURCE_TYPE_CHOICES = [
        ('sap', 'SAP'),
        ('utility', 'Utility'),
        ('travel', 'Travel'),
    ]
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    category = models.CharField(max_length=100, blank=True, default='')

    SCOPE_CHOICES = [
        ('scope_1', 'Scope 1'),
        ('scope_2', 'Scope 2'),
        ('scope_3', 'Scope 3'),
    ]
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)

    activity_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, default='')
    quantity = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True, default='')
    original_unit = models.CharField(max_length=50, blank=True, default='')
    conversion_factor = models.DecimalField(max_digits=12, decimal_places=6, default=1.0)

    amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True, default='')

    source_metadata = models.JSONField(default=dict, blank=True)

    # Flags
    is_flagged = models.BooleanField(default=False)
    flag_reasons = models.JSONField(default=list, blank=True)
    FLAG_SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    flag_severity = models.CharField(max_length=10, choices=FLAG_SEVERITY_CHOICES, blank=True, default='')

    # Review status
    REVIEW_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('locked', 'Locked'),
    ]
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_records')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True, default='')

    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='locked_records')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source_type} | {self.description[:50]} | {self.review_status}"


class ReviewAction(models.Model):
    """Immutable audit log for all review actions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='review_actions')
    normalized_record = models.ForeignKey(NormalizedRecord, on_delete=models.CASCADE, related_name='review_actions')

    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
        ('unflagged', 'Unflagged'),
        ('locked', 'Locked'),
        ('unlocked', 'Unlocked'),
        ('comment', 'Comment'),
        ('edited', 'Edited'),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    previous_status = models.CharField(max_length=20, blank=True, default='')
    new_status = models.CharField(max_length=20, blank=True, default='')
    comment = models.TextField(blank=True, default='')
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.action} by {self.performed_by} at {self.performed_at}"
