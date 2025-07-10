"""
URL configuration for DataLens Backend project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from inventory.dashboard_views import dashboard_stats

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Endpoints
    path('api/auth/', include('authentication.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/forecasting/', include('forecasting.urls')),
    path('api/alerts/', include('alerts.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/data-import/', include('data_import.urls')),  # Nueva app para importación de datos
    
    # Dashboard
    path('api/dashboard/stats/', dashboard_stats, name='dashboard_stats'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
