from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rules', views.AlertRuleViewSet, basename='alert-rules')
router.register(r'alerts', views.AlertViewSet, basename='alerts')
router.register(r'notifications', views.NotificationLogViewSet, basename='notifications')

urlpatterns = [
    # Custom endpoints
    path('dashboard/', views.AlertsDashboardView.as_view(), name='alerts_dashboard'),
    path('check-alerts/', views.CheckAlertsView.as_view(), name='check_alerts'),
    path('test-rule/<int:rule_id>/', views.TestAlertRuleView.as_view(), name='test_alert_rule'),
    
    # ViewSets (incluye los endpoints de acknowledge, resolve, dismiss automáticamente)
    path('', include(router.urls)),
]
