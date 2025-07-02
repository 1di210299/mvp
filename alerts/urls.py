from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rules', views.AlertRuleViewSet)
router.register(r'alerts', views.AlertViewSet)
router.register(r'notifications', views.NotificationLogViewSet)

urlpatterns = [
    # Custom endpoints
    path('dashboard/', views.AlertsDashboardView.as_view(), name='alerts_dashboard'),
    path('alerts/<int:alert_id>/acknowledge/', views.AcknowledgeAlertView.as_view(), name='acknowledge_alert'),
    path('alerts/<int:alert_id>/resolve/', views.ResolveAlertView.as_view(), name='resolve_alert'),
    path('check-alerts/', views.CheckAlertsView.as_view(), name='check_alerts'),
    path('test-rule/<int:rule_id>/', views.TestAlertRuleView.as_view(), name='test_alert_rule'),
    
    # ViewSets
    path('', include(router.urls)),
]
