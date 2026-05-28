from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import TenantAccessPermission
from review.models import NormalizedRecord


class DashboardSummaryView(APIView):
    """
    Returns aggregate statistics for the dashboard.
    
    GET /api/dashboard/summary/
    Response: {total, pending, approved, rejected, flagged, locked, by_scope, by_source}
    """
    permission_classes = [TenantAccessPermission]

    def get(self, request):
        tenant = request.user.tenant
        qs = NormalizedRecord.objects.filter(tenant=tenant)

        # Status counts
        status_counts = qs.values('review_status').annotate(count=Count('id'))
        status_map = {item['review_status']: item['count'] for item in status_counts}

        total = sum(status_map.values())
        flagged = qs.filter(is_flagged=True).count()

        # By scope
        scope_data = list(
            qs.values('scope')
            .annotate(count=Count('id'))
            .order_by('scope')
        )

        # By source
        source_data = list(
            qs.values('source_type')
            .annotate(count=Count('id'))
            .order_by('source_type')
        )

        # Rename fields for frontend
        by_scope = [{'scope': s['scope'].replace('_', ' ').title(), 'count': s['count']} for s in scope_data]
        by_source = [{'source': s['source_type'], 'count': s['count']} for s in source_data]

        return Response({
            'total': total,
            'pending': status_map.get('pending', 0),
            'approved': status_map.get('approved', 0),
            'rejected': status_map.get('rejected', 0),
            'locked': status_map.get('locked', 0),
            'flagged': flagged,
            'by_scope': by_scope,
            'by_source': by_source,
        })
