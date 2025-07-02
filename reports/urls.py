from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'templates', views.ReportTemplateViewSet)
router.register(r'reports', views.ReportViewSet)
router.register(r'kpis', views.KPIDefinitionViewSet)
router.register(r'kpi-values', views.KPIValueViewSet)
router.register(r'schedules', views.ReportScheduleViewSet)

urlpatterns = [
    # Custom endpoints
    path('generate/', views.GenerateReportView.as_view(), name='generate_report'),
    path('reports/<int:report_id>/download/', views.DownloadReportView.as_view(), name='download_report'),
    path('dashboard/', views.ReportsDashboardView.as_view(), name='reports_dashboard'),
    path('kpis/calculate/', views.CalculateKPIsView.as_view(), name='calculate_kpis'),
    path('export/', views.ExportDataView.as_view(), name='export_data'),
    
    # ViewSets
    path('', include(router.urls)),
]
