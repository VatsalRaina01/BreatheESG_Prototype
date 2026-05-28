from rest_framework import serializers
from .models import NormalizedRecord, ReviewAction


class ReviewActionSerializer(serializers.ModelSerializer):
    performed_by_email = serializers.EmailField(source='performed_by.email', read_only=True, default='')

    class Meta:
        model = ReviewAction
        fields = [
            'id', 'action', 'previous_status', 'new_status',
            'comment', 'performed_by_email', 'performed_at', 'changes',
        ]
        read_only_fields = fields


class NormalizedRecordSerializer(serializers.ModelSerializer):
    """List view serializer — lightweight."""

    class Meta:
        model = NormalizedRecord
        fields = [
            'id', 'source_type', 'category', 'scope',
            'activity_date', 'description', 'quantity', 'unit',
            'original_unit', 'amount', 'currency',
            'is_flagged', 'flag_reasons', 'flag_severity',
            'review_status', 'created_at',
        ]
        read_only_fields = fields


class NormalizedRecordDetailSerializer(serializers.ModelSerializer):
    """Detail view serializer — includes raw data and audit trail."""
    raw_data = serializers.SerializerMethodField()
    audit_trail = serializers.SerializerMethodField()

    class Meta:
        model = NormalizedRecord
        fields = [
            'id', 'source_type', 'category', 'scope',
            'activity_date', 'description', 'quantity', 'unit',
            'original_unit', 'conversion_factor', 'amount', 'currency',
            'source_metadata',
            'is_flagged', 'flag_reasons', 'flag_severity',
            'review_status', 'reviewed_by', 'reviewed_at', 'review_comment',
            'locked_at', 'created_at', 'updated_at',
            'raw_data', 'audit_trail',
        ]
        read_only_fields = fields

    def get_raw_data(self, obj):
        try:
            return obj.raw_record.raw_data
        except Exception:
            return {}

    def get_audit_trail(self, obj):
        actions = obj.review_actions.order_by('performed_at')
        return ReviewActionSerializer(actions, many=True).data
