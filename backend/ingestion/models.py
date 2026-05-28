import uuid
from django.db import models
from core.models import Tenant, User


class DataSource(models.Model):
    """A configured data source (e.g., 'SAP Munich Plant', 'ComEd Portal')."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='data_sources')

    SOURCE_TYPE_CHOICES = [
        ('sap', 'SAP'),
        ('utility', 'Utility'),
        ('travel', 'Travel'),
    ]
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class IngestionJob(models.Model):
    """Tracks a single file upload + processing run."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='ingestion_jobs')
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='jobs')
    file_name = models.CharField(max_length=500)
    file_hash = models.CharField(max_length=64, blank=True, default='')

    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')

    total_rows = models.IntegerField(default=0)
    parsed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    flagged_rows = models.IntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    error_log = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.file_name} ({self.status})"


class RawRecord(models.Model):
    """Stores the original row exactly as received. Never modified after creation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='raw_records')
    ingestion_job = models.ForeignKey(IngestionJob, on_delete=models.CASCADE, related_name='raw_records')
    row_number = models.IntegerField()
    raw_data = models.JSONField()

    PARSE_STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
    ]
    parse_status = models.CharField(max_length=10, choices=PARSE_STATUS_CHOICES, default='success')
    parse_errors = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['row_number']

    def __str__(self):
        return f"Row {self.row_number} ({self.parse_status})"
