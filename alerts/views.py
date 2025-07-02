from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import AlertRule, Alert, NotificationLog


# Stubs temporales para alerts
class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.none()
    def list(self, request): return Response([])

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.none()
    def list(self, request): return Response([])

class NotificationLogViewSet(viewsets.ModelViewSet):
    queryset = NotificationLog.objects.none()
    def list(self, request): return Response([])

class AlertsDashboardView(APIView):
    def get(self, request): return Response({'message': 'En desarrollo'})

class AcknowledgeAlertView(APIView):
    def post(self, request, alert_id): return Response({'message': 'En desarrollo'})

class ResolveAlertView(APIView):
    def post(self, request, alert_id): return Response({'message': 'En desarrollo'})

class CheckAlertsView(APIView):
    def post(self, request): return Response({'message': 'En desarrollo'})

class TestAlertRuleView(APIView):
    def post(self, request, rule_id): return Response({'message': 'En desarrollo'})
