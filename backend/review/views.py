from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from core.permissions import TenantAccessPermission
from .models import NormalizedRecord, ReviewAction
from .serializers import NormalizedRecordSerializer, NormalizedRecordDetailSerializer


class NormalizedRecordViewSet(viewsets.ModelViewSet):
    """
    Records endpoint with filtering, search, and review actions.
    
    Filters: source_type, scope, review_status, is_flagged
    Search: description
    Ordering: activity_date, created_at, quantity
    """
    permission_classes = [TenantAccessPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['source_type', 'scope', 'review_status', 'is_flagged']
    search_fields = ['description', 'category']
    ordering_fields = ['activity_date', 'created_at', 'quantity', 'review_status']
    ordering = ['-created_at']

    def get_queryset(self):
        return NormalizedRecord.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('raw_record')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NormalizedRecordDetailSerializer
        return NormalizedRecordSerializer

    def _log_action(self, record, action_type, comment='', previous_status=''):
        """Create an immutable audit log entry."""
        ReviewAction.objects.create(
            tenant=record.tenant,
            normalized_record=record,
            action=action_type,
            previous_status=previous_status,
            new_status=record.review_status,
            comment=comment,
            performed_by=self.request.user,
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a record."""
        record = self.get_object()
        if record.review_status == 'locked':
            return Response(
                {'error': 'Cannot modify a locked record.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous = record.review_status
        record.review_status = 'approved'
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.review_comment = request.data.get('comment', '')
        record.save()

        self._log_action(record, 'approved', request.data.get('comment', ''), previous)

        return Response({'status': 'approved', 'id': str(record.id)})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a record."""
        record = self.get_object()
        if record.review_status == 'locked':
            return Response(
                {'error': 'Cannot modify a locked record.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comment = request.data.get('comment', '')
        previous = record.review_status
        record.review_status = 'rejected'
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.review_comment = comment
        record.save()

        self._log_action(record, 'rejected', comment, previous)

        return Response({'status': 'rejected', 'id': str(record.id)})

    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        """Manually flag a record."""
        record = self.get_object()
        if record.review_status == 'locked':
            return Response(
                {'error': 'Cannot modify a locked record.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reasons = request.data.get('reasons', [])
        if isinstance(reasons, str):
            reasons = [reasons]

        record.is_flagged = True
        record.flag_reasons = list(set(record.flag_reasons + reasons))
        record.flag_severity = request.data.get('severity', 'warning')
        record.save()

        self._log_action(record, 'flagged', f"Flagged: {', '.join(reasons)}")

        return Response({'status': 'flagged', 'id': str(record.id)})

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """Lock a record for audit."""
        record = self.get_object()
        if record.review_status != 'approved':
            return Response(
                {'error': 'Only approved records can be locked.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous = record.review_status
        record.review_status = 'locked'
        record.locked_at = timezone.now()
        record.locked_by = request.user
        record.save()

        self._log_action(record, 'locked', '', previous)

        return Response({'status': 'locked', 'id': str(record.id)})

    @action(detail=False, methods=['post'], url_path='bulk-approve')
    def bulk_approve(self, request):
        """Approve multiple records at once."""
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': 'No record IDs provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = self.get_queryset().filter(
            id__in=ids,
            review_status__in=['pending', 'rejected'],
        )

        count = 0
        for record in records:
            previous = record.review_status
            record.review_status = 'approved'
            record.reviewed_by = request.user
            record.reviewed_at = timezone.now()
            record.save()
            self._log_action(record, 'approved', 'Bulk approved', previous)
            count += 1

        return Response({'approved': count})

    @action(detail=False, methods=['post'], url_path='bulk-reject')
    def bulk_reject(self, request):
        """Reject multiple records at once."""
        ids = request.data.get('ids', [])
        comment = request.data.get('comment', '')

        if not ids:
            return Response(
                {'error': 'No record IDs provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = self.get_queryset().filter(
            id__in=ids,
            review_status__in=['pending', 'approved'],
        )

        count = 0
        for record in records:
            previous = record.review_status
            record.review_status = 'rejected'
            record.reviewed_by = request.user
            record.reviewed_at = timezone.now()
            record.review_comment = comment
            record.save()
            self._log_action(record, 'rejected', comment or 'Bulk rejected', previous)
            count += 1

        return Response({'rejected': count})
