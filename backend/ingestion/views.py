from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import TenantAccessPermission
from .models import DataSource, IngestionJob
from .serializers import DataSourceSerializer, IngestionJobSerializer
from .pipeline import IngestionPipeline


class DataSourceViewSet(viewsets.ModelViewSet):
    """CRUD for data sources. Filtered by tenant."""
    serializer_class = DataSourceSerializer
    permission_classes = [TenantAccessPermission]

    def get_queryset(self):
        return DataSource.objects.filter(tenant=self.request.user.tenant)


class IngestionJobViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve ingestion jobs. Filtered by tenant."""
    serializer_class = IngestionJobSerializer
    permission_classes = [TenantAccessPermission]

    def get_queryset(self):
        return IngestionJob.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('data_source', 'uploaded_by')


class UploadView(APIView):
    """
    Upload a data file for processing.
    
    POST /api/ingest/upload/
    - file: the CSV/TXT file (multipart)
    - data_source_id: UUID of the data source
    - source_type: sap|utility|travel (fallback if no data_source_id)
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [TenantAccessPermission]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get data source
        data_source_id = request.data.get('data_source_id')
        source_type = request.data.get('source_type')

        if data_source_id:
            try:
                data_source = DataSource.objects.get(
                    id=data_source_id,
                    tenant=request.user.tenant,
                )
                source_type = data_source.source_type
            except DataSource.DoesNotExist:
                return Response(
                    {'error': 'Data source not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif source_type:
            # Auto-create a default data source
            data_source, _ = DataSource.objects.get_or_create(
                tenant=request.user.tenant,
                source_type=source_type,
                name=f"Default {source_type.upper()} Source",
                defaults={'created_by': request.user},
            )
        else:
            return Response(
                {'error': 'Either data_source_id or source_type is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if source_type not in ('sap', 'utility', 'travel'):
            return Response(
                {'error': f"Invalid source type: {source_type}. Must be sap, utility, or travel."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create ingestion job
        job = IngestionJob.objects.create(
            tenant=request.user.tenant,
            data_source=data_source,
            file_name=file.name,
            uploaded_by=request.user,
            status='processing',
        )

        # Run pipeline
        try:
            pipeline = IngestionPipeline(job, source_type)
            stats = pipeline.process(file)

            return Response({
                'job_id': str(job.id),
                'file_name': file.name,
                'status': job.status,
                'total_rows': stats['total_rows'],
                'parsed_rows': stats['parsed_rows'],
                'failed_rows': stats['failed_rows'],
                'flagged_rows': stats['flagged_rows'],
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'job_id': str(job.id),
                'file_name': file.name,
                'status': 'failed',
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
