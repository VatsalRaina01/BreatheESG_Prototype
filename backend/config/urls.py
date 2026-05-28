"""
Breathe ESG — URL Configuration

All API endpoints are under /api/ prefix.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/', include('ingestion.urls')),
    path('api/', include('review.urls')),
    path('api/', include('dashboard.urls')),
]
