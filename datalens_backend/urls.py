"""
URL configuration for DataLens Backend project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from inventory.dashboard_views import dashboard_stats
from marketing_views import marketing_page

def redirect_to_frontend(request):
    """Redirige rutas del backend al frontend correspondiente"""
    return redirect('http://localhost:3000/')

def redirect_dashboard(request):
    """Redirige dashboard al frontend"""
    return redirect('http://localhost:3000/app/dashboard')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Marketing page - Primera página que se ve
    path('', marketing_page, name='home'),
    path('marketing/', marketing_page, name='marketing'),
    
    # Redirects to frontend for common routes
    path('dashboard/', redirect_dashboard, name='dashboard_redirect'),
    path('products/', lambda request: redirect('http://localhost:3000/app/products'), name='products_redirect'),
    path('categories/', lambda request: redirect('http://localhost:3000/app/categories'), name='categories_redirect'),
    path('suppliers/', lambda request: redirect('http://localhost:3000/app/suppliers'), name='suppliers_redirect'),
    path('inventory/', lambda request: redirect('http://localhost:3000/app/inventory'), name='inventory_redirect'),
    path('transactions/', lambda request: redirect('http://localhost:3000/app/transactions'), name='transactions_redirect'),
    path('alerts/', lambda request: redirect('http://localhost:3000/app/alerts'), name='alerts_redirect'),
    path('forecasting/', lambda request: redirect('http://localhost:3000/app/forecasting'), name='forecasting_redirect'),
    path('reports/', lambda request: redirect('http://localhost:3000/app/reports'), name='reports_redirect'),
    path('data-import/', lambda request: redirect('http://localhost:3000/app/data-import'), name='data_import_redirect'),
    path('customers/', lambda request: redirect('http://localhost:3000/app/customers'), name='customers_redirect'),
    path('leads/', lambda request: redirect('http://localhost:3000/app/leads'), name='leads_redirect'),
    path('opportunities/', lambda request: redirect('http://localhost:3000/app/opportunities'), name='opportunities_redirect'),
    path('settings/', lambda request: redirect('http://localhost:3000/app/settings'), name='settings_redirect'),
    path('login/', lambda request: redirect('http://localhost:3000/login'), name='login_redirect'),
    
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
    path('api/data-import/', include('data_import.urls')),
    path('api/intelligence/', include('intelligence.urls')),
    
    # ✅ NUEVO: WhatsApp API
    path('api/whatsapp/', include('inventory.urls.whatsapp_urls')),
    
    # ✅ NUEVO: Configuración de empresa - ahora incluida en auth URLs
    # path('api/company/', include('authentication.urls.company')),
    
    # Dashboard API - Ruta directa para frontend
    path('api/dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    
    # Dashboard API
    path('api/dashboard/stats/', dashboard_stats, name='dashboard_stats'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
