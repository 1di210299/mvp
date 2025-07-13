from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rules', views.AlertRuleViewSet, basename='alert-rules')
router.register(r'alerts', views.AlertViewSet, basename='alerts')
router.register(r'notifications', views.NotificationLogViewSet, basename='notifications')
router.register(r'recipients', views.AlertRecipientViewSet, basename='alert-recipients')

urlpatterns = [
    # Custom endpoints
    path('dashboard/', views.AlertsDashboardView.as_view(), name='alerts_dashboard'),
    path('check-alerts/', views.CheckAlertsView.as_view(), name='check_alerts'),
    path('test-rule/<int:rule_id>/', views.TestAlertRuleView.as_view(), name='test_alert_rule'),
    
    # Notification endpoints
    path('test-notifications/', views.TestNotificationServicesView.as_view(), name='test_notifications'),
    path('notification-settings/', views.NotificationSettingsView.as_view(), name='notification_settings'),
    
    # ViewSets (incluye los endpoints de acknowledge, resolve, dismiss automáticamente)
    path('', include(router.urls)),
]
