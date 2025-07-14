from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para las vistas basadas en clase
router = DefaultRouter()

# URLs para las vistas del app de inteligencia
urlpatterns = [
    # Briefing matutino
    path('briefing/morning/', views.MorningBriefingView.as_view(), name='morning-briefing'),
    path('briefing/history/', views.BriefingHistoryView.as_view(), name='briefing-history'),
    
    # Insights
    path('insights/', views.InsightsView.as_view(), name='insights'),
    path('insights/<int:insight_id>/resolve/', views.resolve_insight, name='resolve-insight'),
    
    # Métricas
    path('metrics/', views.MetricsView.as_view(), name='metrics'),
    
    # Dashboard intelligence (endpoint principal)
    path('dashboard/', views.dashboard_intelligence, name='dashboard-intelligence'),
    
    # Estado del servicio
    path('status/', views.intelligence_status, name='intelligence-status'),
    
    # Incluir rutas del router
    path('', include(router.urls)),
]

# Agregar namespace para el app
app_name = 'intelligence' 