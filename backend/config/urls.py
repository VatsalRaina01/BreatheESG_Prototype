"""
URL configuration for Breathe ESG backend.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("core.urls")),
    path("api/", include("ingestion.urls")),
    path("api/", include("review.urls")),
    path("api/", include("dashboard.urls")),
]
