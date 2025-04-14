# api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .authentication import CustomTokenObtainPairView
from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'business-rules', views.BusinessRuleViewSet, basename='business-rule')
router.register(r'agent-actions', views.AgentActionViewSet, basename='agent-action')
router.register(r'business-contexts', views.BusinessContextViewSet, basename='business-context')

urlpatterns = [
    # Rutas de autenticación
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', views.register_user, name='register_user'),
    
    # Rutas de datasets
    path('datasets/', views.dataset_list, name='dataset_list'),
    path('datasets/<int:pk>/', views.dataset_detail, name='dataset_detail'),
    path('datasets/<int:dataset_id>/context/', views.get_dataset_context, name='get_dataset_context'),
    
    # Rutas de carga y conexión
    path('upload-dataset/', views.upload_dataset, name='upload_dataset'),
    path('test-connection/', views.test_connection, name='test_connection'),
    
    # Rutas de visualización y análisis
    path('generate-chart/', views.generate_chart, name='generate_chart'),
    path('generate-sales-visualization/', views.generate_sales_visualization, name='generate_sales_visualization'),
    path('predict-sales/', views.predict_sales_view, name='predict_sales'),
    
    # Rutas de asistente y NLP
    path('assistant/analyze/', views.assistant_analyze, name='assistant_analyze'),
    path('nlp/sentiment/', views.analyze_sentiment, name='analyze_sentiment'),
    path('nlp/classify-feedback/', views.classify_feedback, name='classify_feedback'),
    path('nlp/business-analysis/', views.business_analysis, name='business_analysis'),
    path('nlp/financial-terms/', views.explain_financial_terms, name='explain_financial_terms'),
    path('agent/', include(router.urls)),
    path('agent/actions/approve/<int:action_id>/', views.approve_agent_action, name='approve-agent-action'),
    path('agent/actions/reject/<int:action_id>/', views.reject_agent_action, name='reject-agent-action'),
    path('monitor/analyze/', views.analyze_dataset, name='analyze_dataset'),
    path('monitor/alerts/<int:dataset_id>/', views.get_active_alerts, name='get_active_alerts'),
    path('monitor/actions/<int:dataset_id>/', views.get_suggested_actions, name='get_suggested_actions'),
    path('monitor/alerts/resolve/<int:alert_id>/', views.resolve_alert, name='resolve_alert'),
]