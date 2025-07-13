from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'templates', views.ReportTemplateViewSet, basename='report_template')
router.register(r'reports', views.ReportViewSet, basename='report')
router.register(r'kpis', views.KPIDefinitionViewSet, basename='kpi_definition')
router.register(r'kpi-values', views.KPIValueViewSet, basename='kpi_value')
router.register(r'schedules', views.ReportScheduleViewSet, basename='report_schedule')

urlpatterns = [
    # Custom endpoints
    path('generate/', views.GenerateReportView.as_view(), name='generate_report'),
    path('reports/<int:report_id>/download/', views.DownloadReportView.as_view(), name='download_report'),
    path('dashboard/', views.ReportsDashboardView.as_view(), name='reports_dashboard'),
    path('kpis/calculate/', views.CalculateKPIsView.as_view(), name='calculate_kpis'),
    path('export/', views.ExportDataView.as_view(), name='export_data'),
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics-dashboard'),
    
    # NUEVOS ENDPOINTS PARA EXPORTACIÓN REAL
    path('export/pdf/', views.ExportPDFView.as_view(), name='export_pdf'),
    path('export/excel/', views.ExportExcelView.as_view(), name='export_excel'),
    
    # ENDPOINT PARA INFORMACIÓN DEL SISTEMA
    path('system-info/', views.SystemInfoView.as_view(), name='system_info'),
    
    # Mock endpoint para desarrollo
    path('mock-download/', views.MockDownloadReportView.as_view(), name='mock_download_report'),

    # ViewSets
    path('', include(router.urls)),
]
