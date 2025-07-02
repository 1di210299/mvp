from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import AlertRule, Alert, NotificationLog
from .serializers import (
    AlertRuleSerializer, AlertSerializer, NotificationLogSerializer,
    AlertDashboardSerializer, AlertActionSerializer
)
from .tasks import check_alert_rule, check_all_alerts


class AlertRuleViewSet(viewsets.ModelViewSet):
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AlertRule.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def test_rule(self, request, pk=None):
        """Probar una regla de alerta específica"""
        try:
            rule = self.get_object()
            task = check_alert_rule.delay(rule.id)
            return Response({
                'message': 'Prueba de regla iniciada',
                'task_id': task.id
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activar/desactivar una regla de alerta"""
        try:
            rule = self.get_object()
            rule.is_active = not rule.is_active
            rule.save()
            return Response({
                'message': f'Regla {"activada" if rule.is_active else "desactivada"}',
                'is_active': rule.is_active
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Alert.objects.filter(company=self.request.user.company)
        
        # Filtros opcionales
        status_filter = self.request.query_params.get('status')
        severity_filter = self.request.query_params.get('severity')
        product_filter = self.request.query_params.get('product')
        location_filter = self.request.query_params.get('location')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if severity_filter:
            queryset = queryset.filter(severity=severity_filter)
        if product_filter:
            queryset = queryset.filter(product_id=product_filter)
        if location_filter:
            queryset = queryset.filter(location_id=location_filter)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Reconocer una alerta"""
        try:
            alert = self.get_object()
            serializer = AlertActionSerializer(data=request.data)
            
            if serializer.is_valid():
                alert.acknowledge(request.user)
                
                # Agregar nota si se proporciona
                note = serializer.validated_data.get('note')
                if note:
                    if not alert.context_data:
                        alert.context_data = {}
                    alert.context_data['acknowledgment_note'] = note
                    alert.save()
                
                return Response({
                    'message': 'Alerta reconocida exitosamente',
                    'status': alert.status
                })
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolver una alerta"""
        try:
            alert = self.get_object()
            serializer = AlertActionSerializer(data=request.data)
            
            if serializer.is_valid():
                alert.resolve(request.user)
                
                # Agregar nota si se proporciona
                note = serializer.validated_data.get('note')
                if note:
                    if not alert.context_data:
                        alert.context_data = {}
                    alert.context_data['resolution_note'] = note
                    alert.save()
                
                return Response({
                    'message': 'Alerta resuelta exitosamente',
                    'status': alert.status
                })
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Descartar una alerta"""
        try:
            alert = self.get_object()
            serializer = AlertActionSerializer(data=request.data)
            
            if serializer.is_valid():
                alert.dismiss(request.user)
                
                # Agregar nota si se proporciona
                note = serializer.validated_data.get('note')
                if note:
                    if not alert.context_data:
                        alert.context_data = {}
                    alert.context_data['dismissal_note'] = note
                    alert.save()
                
                return Response({
                    'message': 'Alerta descartada exitosamente',
                    'status': alert.status
                })
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return NotificationLog.objects.filter(
            alert__company=self.request.user.company
        ).order_by('-created_at')


class AlertsDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Dashboard de alertas con estadísticas y métricas"""
        try:
            company = request.user.company
            
            # Estadísticas básicas
            total_alerts = Alert.objects.filter(company=company).count()
            active_alerts = Alert.objects.filter(
                company=company, 
                status='active'
            ).count()
            critical_alerts = Alert.objects.filter(
                company=company,
                severity='critical',
                status__in=['active', 'acknowledged']
            ).count()
            acknowledged_alerts = Alert.objects.filter(
                company=company,
                status='acknowledged'
            ).count()
            resolved_alerts = Alert.objects.filter(
                company=company,
                status='resolved'
            ).count()
            
            # Alertas por severidad
            alerts_by_severity = Alert.objects.filter(
                company=company,
                status__in=['active', 'acknowledged']
            ).values('severity').annotate(count=Count('id'))
            
            severity_dict = {item['severity']: item['count'] for item in alerts_by_severity}
            
            # Alertas por tipo
            alerts_by_type = Alert.objects.filter(
                company=company,
                status__in=['active', 'acknowledged']
            ).values('rule__alert_type').annotate(count=Count('id'))
            
            type_dict = {
                item['rule__alert_type']: item['count'] 
                for item in alerts_by_type if item['rule__alert_type']
            }
            
            # Alertas recientes (últimas 10)
            recent_alerts = Alert.objects.filter(
                company=company
            ).order_by('-created_at')[:10]
            
            # Tendencias (últimos 7 días)
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=6)
            
            alert_trends = {}
            for i in range(7):
                date = start_date + timedelta(days=i)
                count = Alert.objects.filter(
                    company=company,
                    created_at__date=date
                ).count()
                alert_trends[date.strftime('%Y-%m-%d')] = count
            
            data = {
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'critical_alerts': critical_alerts,
                'acknowledged_alerts': acknowledged_alerts,
                'resolved_alerts': resolved_alerts,
                'alerts_by_severity': severity_dict,
                'alerts_by_type': type_dict,
                'recent_alerts': AlertSerializer(recent_alerts, many=True).data,
                'alert_trends': alert_trends
            }
            
            serializer = AlertDashboardSerializer(data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckAlertsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Verificar todas las reglas de alerta manualmente"""
        try:
            task = check_all_alerts.delay()
            return Response({
                'message': 'Verificación de alertas iniciada',
                'task_id': task.id
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestAlertRuleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, rule_id):
        """Probar una regla de alerta específica"""
        try:
            # Verificar que la regla pertenece a la empresa del usuario
            rule = AlertRule.objects.get(
                id=rule_id,
                company=request.user.company
            )
            
            task = check_alert_rule.delay(rule.id)
            return Response({
                'message': f'Prueba de regla "{rule.name}" iniciada',
                'task_id': task.id
            })
        except AlertRule.DoesNotExist:
            return Response(
                {'error': 'Regla de alerta no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
