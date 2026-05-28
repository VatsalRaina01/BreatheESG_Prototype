from rest_framework import serializers
from .models import DataSource, IngestionJob, RawRecord


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ['id', 'source_type', 'name', 'description', 'config', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['tenant'] = request.user.tenant
        validated_data['created_by'] = request.user
        return super().create(validated_data)


class IngestionJobSerializer(serializers.ModelSerializer):
    data_source_type = serializers.CharField(source='data_source.source_type', read_only=True)
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    uploaded_by_email = serializers.EmailField(source='uploaded_by.email', read_only=True, default='')

    class Meta:
        model = IngestionJob
        fields = [
            'id', 'file_name', 'file_hash', 'status',
            'total_rows', 'parsed_rows', 'failed_rows', 'flagged_rows',
            'started_at', 'completed_at',
            'data_source_type', 'data_source_name', 'uploaded_by_email',
            'error_log',
        ]
        read_only_fields = fields
