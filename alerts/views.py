from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging
from .models import AlertRule, Alert, NotificationLog
from .serializers import (
    AlertRuleSerializer, AlertSerializer, NotificationLogSerializer,
    AlertDashboardSerializer, AlertActionSerializer
)
from .tasks import check_alert_rule, check_all_alerts, test_notification_services
from .services import AlertService, notification_service  # ✅ Importación corregida

logger = logging.getLogger(__name__)


class AlertRuleViewSet(viewsets.ModelViewSet):
    serializer_class = AlertRuleSerializer
    
    def get_queryset(self):
        return AlertRule.objects.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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

    @action(detail=True, methods=['post'])
    def test_notifications(self, request, pk=None):
        """Probar las notificaciones de una regla específica"""
        try:
            rule = self.get_object()
            
            # Crear una alerta de prueba
            from inventory.models import Product
            test_product = Product.objects.filter(company=rule.company).first()
            
            if not test_product:
                return Response({
                    'error': 'No hay productos disponibles para la prueba'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Crear alerta de prueba temporal
            test_alert = Alert(
                company=rule.company,
                rule=rule,
                product=test_product,
                title=f"🧪 PRUEBA: {rule.name}",
                message="Esta es una alerta de prueba del sistema DataLens. Si recibe este mensaje, las notificaciones están funcionando correctamente.",
                severity='low',
                current_value=10,
                threshold_value=5,
                status='active'
            )
            
            # No guardar en base de datos, solo usar para prueba
            notification_type = request.data.get('notification_type', 'all')
            results = notification_service.send_alert_notification(test_alert, notification_type)
            
            return Response({
                'message': 'Prueba de notificaciones completada',
                'results': results
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    
    def get_queryset(self):
        return Alert.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return Response({'status': 'alert acknowledged'})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.status = 'resolved'
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.save()
        return Response({'status': 'alert resolved'})
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        alert = self.get_object()
        alert.status = 'dismissed'
        alert.dismissed_by = request.user
        alert.dismissed_at = timezone.now()
        alert.save()
        return Response({'status': 'alert dismissed'})

    @action(detail=True, methods=['post'])
    def resend_notifications(self, request, pk=None):
        """Reenviar notificaciones para una alerta"""
        try:
            alert = self.get_object()
            notification_type = request.data.get('notification_type', 'all')
            
            results = notification_service.send_alert_notification(alert, notification_type)
            
            return Response({
                'message': 'Notificaciones reenviadas',
                'results': results
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NotificationLog.objects.all().order_by('-sent_at')
    serializer_class = NotificationLogSerializer

    def get_queryset(self):
        queryset = NotificationLog.objects.filter(
            alert__company=self.request.user.company
        ).order_by('-created_at')
        
        # Filtros opcionales
        notification_type = self.request.query_params.get('type')
        status_filter = self.request.query_params.get('status')
        alert_id = self.request.query_params.get('alert_id')
        
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if alert_id:
            queryset = queryset.filter(alert_id=alert_id)
        
        return queryset


class AlertsDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Dashboard de alertas con estadísticas y métricas"""
        try:
            # Obtener alertas sin filtro de company por ahora (para testing)
            # En producción, usar: Alert.objects.filter(company=request.user.company)
            
            # Estadísticas básicas
            total_alerts = Alert.objects.count()
            active_alerts = Alert.objects.filter(status='active').count()
            critical_alerts = Alert.objects.filter(
                severity='critical',
                status__in=['active', 'acknowledged']
            ).count()
            acknowledged_alerts = Alert.objects.filter(status='acknowledged').count()
            resolved_alerts = Alert.objects.filter(status='resolved').count()
            
            # Alertas por severidad
            alerts_by_severity = Alert.objects.filter(
                status__in=['active', 'acknowledged']
            ).values('severity').annotate(count=Count('id'))
            
            severity_dict = {item['severity']: item['count'] for item in alerts_by_severity}
            
            # Alertas por tipo (basado en regla o source)
            alerts_by_type = {}
            
            # Contar por source como alternativa
            alerts_by_source = Alert.objects.filter(
                status__in=['active', 'acknowledged']
            ).values('source').annotate(count=Count('id'))
            
            for item in alerts_by_source:
                source_map = {
                    'rule': 'low_stock',
                    'forecast': 'high_demand', 
                    'system': 'negative_stock'
                }
                alert_type = source_map.get(item['source'], item['source'])
                alerts_by_type[alert_type] = item['count']
            
            # Estadísticas de notificaciones
            notification_stats = NotificationLog.objects.values(
                'notification_type', 'status'
            ).annotate(count=Count('id'))
            
            notification_dict = {}
            for stat in notification_stats:
                ntype = stat['notification_type']
                nstatus = stat['status']
                if ntype not in notification_dict:
                    notification_dict[ntype] = {}
                notification_dict[ntype][nstatus] = stat['count']
            
            # Alertas recientes (últimas 10)
            recent_alerts = Alert.objects.order_by('-created_at')[:10]
            
            # Tendencias (últimos 7 días)
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=6)
            
            alert_trends = {}
            for i in range(7):
                date = start_date + timedelta(days=i)
                count = Alert.objects.filter(created_at__date=date).count()
                alert_trends[date.strftime('%Y-%m-%d')] = count
            
            data = {
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'critical_alerts': critical_alerts,
                'acknowledged_alerts': acknowledged_alerts,
                'resolved_alerts': resolved_alerts,
                'alerts_by_severity': severity_dict,
                'alerts_by_type': alerts_by_type,
                'notification_stats': notification_dict,
                'recent_alerts': AlertSerializer(recent_alerts, many=True).data,
                'alert_trends': alert_trends
            }
            
            return Response(data)
            
        except Exception as e:
            logger.error(f"Error en AlertsDashboardView: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckAlertsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Verificar todas las reglas de alerta manualmente y reenviar notificaciones para alertas activas"""
        try:
            resend_notifications = request.data.get('resend_notifications', True)  # Por defecto True
            
            # Intentar usar Celery primero, si falla ejecutar síncronamente
            try:
                from celery.app.control import Inspect
                from datalens_backend.celery import app
                
                # Verificar si Celery está disponible
                inspect = Inspect(app=app)
                active_workers = inspect.active()
                
                if active_workers:
                    # Celery está activo, usar tarea asíncrona
                    task = check_all_alerts.delay()
                    
                    # También reenviar notificaciones para alertas activas si está habilitado
                    notifications_sent = 0
                    if resend_notifications:
                        from .tasks import send_alert_notification
                        
                        # Obtener alertas activas de los últimos 7 días
                        active_alerts = Alert.objects.filter(
                            status__in=['active', 'acknowledged'],
                            created_at__gte=timezone.now() - timedelta(days=7)
                        )
                        
                        for alert in active_alerts:
                            # Enviar notificaciones de forma asíncrona
                            send_alert_notification.delay(alert.id, 'all')
                            notifications_sent += 1
                    
                    return Response({
                        'message': 'Verificación de alertas iniciada (asíncrona)',
                        'task_id': task.id,
                        'mode': 'async',
                        'notifications_sent': notifications_sent if resend_notifications else 0,
                        'resend_notifications': resend_notifications
                    })
                else:
                    raise Exception("No hay workers de Celery activos")
                    
            except Exception as celery_error:
                # Celery no disponible, ejecutar síncronamente
                logger.warning(f"Celery no disponible: {celery_error}. Ejecutando verificación síncrona.")
                
                # Importar servicios necesarios
                from .services import AlertService
                
                # Ejecutar verificación síncrona
                alert_service = AlertService()
                results = alert_service.check_all_alerts_sync()
                
                # También reenviar notificaciones síncronamente si está habilitado
                notifications_sent = 0
                notification_results = {}
                
                if resend_notifications:
                    # Obtener alertas activas de los últimos 7 días
                    active_alerts = Alert.objects.filter(
                        status__in=['active', 'acknowledged'],
                        created_at__gte=timezone.now() - timedelta(days=7)
                    )
                    
                    for alert in active_alerts:
                        try:
                            # Enviar notificaciones síncronamente
                            notification_result = notification_service.send_alert_notification(alert, 'all')
                            notification_results[alert.id] = notification_result
                            notifications_sent += 1
                        except Exception as e:
                            logger.error(f"Error enviando notificación para alerta {alert.id}: {str(e)}")
                            notification_results[alert.id] = {'error': str(e)}
                
                return Response({
                    'message': 'Verificación de alertas completada (síncrona)',
                    'results': results,
                    'mode': 'sync',
                    'notifications_sent': notifications_sent if resend_notifications else 0,
                    'notification_results': notification_results if resend_notifications else {},
                    'resend_notifications': resend_notifications
                })
                
        except Exception as e:
            logger.error(f"Error en CheckAlertsView: {str(e)}")
            return Response(
                {'error': f'Error al verificar alertas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestNotificationServicesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Probar los servicios de notificación"""
        try:
            task = test_notification_services.delay()
            return Response({
                'message': 'Prueba de servicios de notificación iniciada',
                'task_id': task.id
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """Obtener estado actual de los servicios de notificación"""
        try:
            # Probar servicios sincrónicamente para respuesta inmediata
            email_test = notification_service.test_email_connection()
            whatsapp_test = notification_service.test_whatsapp_connection()
            
            return Response({
                'email': email_test,
                'whatsapp': whatsapp_test
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


class NotificationSettingsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener configuraciones de notificación del usuario"""
        try:
            user = request.user
            
            settings_data = {
                'email_notifications': user.email_notifications,
                'whatsapp_notifications': user.whatsapp_notifications,
                'phone': user.phone,
                'email': user.email,
                'notification_services_status': {
                    'email': notification_service.test_email_connection(),
                    'whatsapp': notification_service.test_whatsapp_connection()
                }
            }
            
            return Response(settings_data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Actualizar configuraciones de notificación del usuario"""
        try:
            user = request.user
            
            # Actualizar configuraciones
            if 'email_notifications' in request.data:
                user.email_notifications = request.data['email_notifications']
            
            if 'whatsapp_notifications' in request.data:
                user.whatsapp_notifications = request.data['whatsapp_notifications']
            
            if 'phone' in request.data:
                user.phone = request.data['phone']
            
            user.save()
            
            return Response({
                'message': 'Configuraciones actualizadas exitosamente',
                'email_notifications': user.email_notifications,
                'whatsapp_notifications': user.whatsapp_notifications,
                'phone': user.phone
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
