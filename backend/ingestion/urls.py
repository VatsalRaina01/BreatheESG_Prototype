from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DataSourceViewSet, IngestionJobViewSet, UploadView

router = DefaultRouter()
router.register(r'sources', DataSourceViewSet, basename='datasource')
router.register(r'ingest/jobs', IngestionJobViewSet, basename='ingestionjob')

urlpatterns = [
    path('ingest/upload/', UploadView.as_view(), name='upload'),
    path('', include(router.urls)),
]
