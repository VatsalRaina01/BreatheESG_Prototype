from django.contrib import admin
from .models import NormalizedRecord, ReviewAction


@admin.register(NormalizedRecord)
class NormalizedRecordAdmin(admin.ModelAdmin):
    list_display = ['source_type', 'scope', 'description', 'quantity', 'unit', 'review_status', 'is_flagged', 'activity_date']
    list_filter = ['source_type', 'scope', 'review_status', 'is_flagged']
    search_fields = ['description', 'category']


@admin.register(ReviewAction)
class ReviewActionAdmin(admin.ModelAdmin):
    list_display = ['action', 'performed_by', 'performed_at', 'normalized_record']
    list_filter = ['action']
