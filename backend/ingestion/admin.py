from django.contrib import admin
from .models import DataSource, IngestionJob, RawRecord


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'tenant', 'created_at']
    list_filter = ['source_type', 'tenant']


@admin.register(IngestionJob)
class IngestionJobAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'status', 'total_rows', 'parsed_rows', 'failed_rows', 'started_at']
    list_filter = ['status']


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'row_number', 'parse_status', 'ingestion_job']
    list_filter = ['parse_status']
