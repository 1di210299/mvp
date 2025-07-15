from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging
from .models import AlertRule, Alert, NotificationLog, AlertRecipient
from .serializers import (
    AlertRuleSerializer, AlertSerializer, NotificationLogSerializer,
    AlertDashboardSerializer, AlertActionSerializer, NotificationTestSerializer,
    AlertRecipientSerializer, AlertRecipientListSerializer
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
            
            # 🎯 NUEVA FUNCIONALIDAD: Agregación de alertas por categoría
            # REUTILIZA patrones existentes y extiende para categorías
            alerts_by_category = self._calculate_alerts_by_category()
            category_risk_analysis = self._analyze_category_risks(alerts_by_category)
            
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
                'alert_trends': alert_trends,
                
                # 🎯 NUEVAS MÉTRICAS ESTRATÉGICAS POR CATEGORÍA
                'alerts_by_category': alerts_by_category,
                'category_risk_analysis': category_risk_analysis,
                'category_priorities': self._get_category_priorities(alerts_by_category)
            }
            
            return Response(data)
            
        except Exception as e:
            logger.error(f"Error en AlertsDashboardView: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_alerts_by_category(self):
        """
        📊 Calcular alertas agregadas por categoría
        REUTILIZA patrones de agregación existentes y los especializa
        """
        try:
            from inventory.models import Category, Product
            
            # Obtener alertas activas agrupadas por categoría de producto
            # REUTILIZAR patrón de agregación del dashboard existente
            alerts_by_category_query = Alert.objects.filter(
                status__in=['active', 'acknowledged'],
                product__isnull=False  # Solo alertas con producto asociado
            ).select_related('product', 'product__category').values(
                'product__category__id',
                'product__category__name'
            ).annotate(
                total_alerts=Count('id'),
                critical_alerts=Count('id', filter=Q(severity='critical')),
                warning_alerts=Count('id', filter=Q(severity='warning')),
                info_alerts=Count('id', filter=Q(severity='info')),
                acknowledged_alerts=Count('id', filter=Q(status='acknowledged')),
                active_alerts=Count('id', filter=Q(status='active'))
            ).order_by('-total_alerts')
            
            alerts_by_category = []
            
            for item in alerts_by_category_query:
                if item['product__category__name']:  # Solo categorías válidas
                    
                    # Calcular productos afectados por categoría
                    affected_products = Alert.objects.filter(
                        status__in=['active', 'acknowledged'],
                        product__category__id=item['product__category__id']
                    ).values('product').distinct().count()
                    
                    # Total de productos en la categoría para contexto
                    total_products = Product.objects.filter(
                        category__id=item['product__category__id'],
                        is_active=True
                    ).count()
                    
                    # Calcular porcentaje de productos afectados
                    affected_percentage = (affected_products / total_products * 100) if total_products > 0 else 0
                    
                    # Determinar nivel de riesgo de la categoría
                    risk_level = self._calculate_category_risk_level(
                        item['critical_alerts'],
                        item['total_alerts'],
                        affected_percentage
                    )
                    
                    category_data = {
                        'category_id': item['product__category__id'],
                        'category_name': item['product__category__name'],
                        'total_alerts': item['total_alerts'],
                        'critical_alerts': item['critical_alerts'],
                        'warning_alerts': item['warning_alerts'],
                        'info_alerts': item['info_alerts'],
                        'acknowledged_alerts': item['acknowledged_alerts'],
                        'active_alerts': item['active_alerts'],
                        'affected_products': affected_products,
                        'total_products': total_products,
                        'affected_percentage': round(affected_percentage, 1),
                        'risk_level': risk_level,
                        'priority_score': self._calculate_category_priority_score(item, affected_percentage)
                    }
                    
                    alerts_by_category.append(category_data)
            
            # Incluir categorías sin alertas para vista completa (opcional)
            categories_with_alerts = {item['category_id'] for item in alerts_by_category}
            all_categories = Category.objects.filter(is_active=True).exclude(
                id__in=categories_with_alerts
            )
            
            for category in all_categories:
                total_products = Product.objects.filter(
                    category=category,
                    is_active=True
                ).count()
                
                if total_products > 0:  # Solo incluir categorías con productos
                    alerts_by_category.append({
                        'category_id': category.id,
                        'category_name': category.name,
                        'total_alerts': 0,
                        'critical_alerts': 0,
                        'warning_alerts': 0,
                        'info_alerts': 0,
                        'acknowledged_alerts': 0,
                        'active_alerts': 0,
                        'affected_products': 0,
                        'total_products': total_products,
                        'affected_percentage': 0,
                        'risk_level': 'low',
                        'priority_score': 0
                    })
            
            # Ordenar por score de prioridad (más crítico primero)
            alerts_by_category.sort(key=lambda x: x['priority_score'], reverse=True)
            
            return alerts_by_category
            
        except Exception as e:
            print(f"❌ Error calculando alertas por categoría: {e}")
            return []
    
    def _calculate_category_risk_level(self, critical_alerts, total_alerts, affected_percentage):
        """
        🎯 Determinar nivel de riesgo de una categoría
        NUEVA LÓGICA ESTRATÉGICA para clasificación de riesgo
        """
        # Criterios para clasificación de riesgo
        if critical_alerts >= 3 or affected_percentage >= 50:
            return 'critical'
        elif critical_alerts >= 1 or affected_percentage >= 25 or total_alerts >= 5:
            return 'high'
        elif total_alerts >= 2 or affected_percentage >= 10:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_category_priority_score(self, alert_data, affected_percentage):
        """
        🔢 Calcular score de prioridad para ordenamiento estratégico
        Combina múltiples factores para determinar qué categorías necesitan atención urgente
        """
        score = 0
        
        # Peso por criticidad de alertas
        score += alert_data['critical_alerts'] * 10
        score += alert_data['warning_alerts'] * 5
        score += alert_data['info_alerts'] * 1
        
        # Peso por porcentaje de productos afectados
        score += affected_percentage * 0.5
        
        # Bonus por alto número de alertas activas (sin acknowledged)
        score += alert_data['active_alerts'] * 2
        
        return round(score, 1)
    
    def _analyze_category_risks(self, alerts_by_category):
        """
        🧠 Análisis de riesgos por categoría - estilo Carlos Empresario
        REUTILIZA patrón de insights del IntelligenceService
        """
        if not alerts_by_category:
            return {
                'summary': 'No hay datos de alertas por categoría disponibles',
                'high_risk_categories': [],
                'requires_immediate_attention': [],
                'stable_categories': []
            }
        
        # Categorizar por nivel de riesgo
        high_risk = [cat for cat in alerts_by_category if cat['risk_level'] in ['critical', 'high']]
        medium_risk = [cat for cat in alerts_by_category if cat['risk_level'] == 'medium']
        low_risk = [cat for cat in alerts_by_category if cat['risk_level'] == 'low']
        
        # Identificar categorías que requieren atención inmediata
        immediate_attention = [
            cat for cat in alerts_by_category 
            if cat['critical_alerts'] > 0 or cat['affected_percentage'] > 30
        ]
        
        # Categorías estables (sin problemas)
        stable_categories = [
            cat for cat in alerts_by_category 
            if cat['total_alerts'] == 0 or (cat['total_alerts'] <= 1 and cat['critical_alerts'] == 0)
        ]
        
        # Generar summary estilo briefing
        total_categories = len(alerts_by_category)
        categories_with_alerts = len([cat for cat in alerts_by_category if cat['total_alerts'] > 0])
        
        summary = f"""
        📊 **Análisis de Riesgos por Categoría:**
        
        🎯 **Resumen:** {categories_with_alerts} de {total_categories} categorías tienen alertas activas
        
        🚨 **Alto riesgo:** {len(high_risk)} categorías necesitan atención urgente
        
        ⚠️ **Riesgo medio:** {len(medium_risk)} categorías bajo monitoreo
        
        ✅ **Estables:** {len(stable_categories)} categorías sin problemas críticos
        """.strip()
        
        return {
            'summary': summary,
            'high_risk_categories': [cat['category_name'] for cat in high_risk],
            'medium_risk_categories': [cat['category_name'] for cat in medium_risk],
            'stable_categories': [cat['category_name'] for cat in stable_categories],
            'requires_immediate_attention': immediate_attention,
            'risk_distribution': {
                'critical': len([c for c in alerts_by_category if c['risk_level'] == 'critical']),
                'high': len([c for c in alerts_by_category if c['risk_level'] == 'high']),
                'medium': len([c for c in alerts_by_category if c['risk_level'] == 'medium']),
                'low': len([c for c in alerts_by_category if c['risk_level'] == 'low'])
            }
        }
    
    def _get_category_priorities(self, alerts_by_category):
        """
        📋 Obtener acciones prioritarias por categoría
        Genera lista de acciones inmediatas estilo Carlos Empresario
        """
        priorities = []
        
        # Top 3 categorías que necesitan atención más urgente
        urgent_categories = sorted(
            [cat for cat in alerts_by_category if cat['priority_score'] > 0],
            key=lambda x: x['priority_score'],
            reverse=True
        )[:3]
        
        for i, category in enumerate(urgent_categories, 1):
            if category['critical_alerts'] > 0:
                action = f"Revisar {category['critical_alerts']} productos críticos"
                urgency = 'urgent'
            elif category['active_alerts'] > 2:
                action = f"Resolver {category['active_alerts']} alertas pendientes"
                urgency = 'important'
            else:
                action = f"Monitorear {category['affected_products']} productos con alertas"
                urgency = 'routine'
            
            priorities.append({
                'rank': i,
                'category_name': category['category_name'],
                'category_id': category['category_id'],
                'action': action,
                'urgency': urgency,
                'reason': f"Score de prioridad: {category['priority_score']} - {category['affected_percentage']}% productos afectados",
                'timeline': '24 horas' if urgency == 'urgent' else '3 días' if urgency == 'important' else '1 semana'
            })
        
        return priorities


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


class AlertRecipientViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar destinatarios de alertas"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        # Usar siempre el serializer completo para mantener consistencia
        return AlertRecipientSerializer
    
    def get_queryset(self):
        """Filtrar destinatarios por empresa del usuario"""
        return AlertRecipient.objects.filter(
            company=self.request.user.company
        ).order_by('name')
    
    def perform_create(self, serializer):
        """Crear destinatario con la empresa del usuario"""
        serializer.save(
            company=self.request.user.company,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Activar/desactivar un destinatario"""
        recipient = self.get_object()
        recipient.is_active = not recipient.is_active
        recipient.save()
        
        status_text = "activado" if recipient.is_active else "desactivado"
        return Response({
            'success': True,
            'message': f'Destinatario {status_text} correctamente',
            'is_active': recipient.is_active
        })
    
    @action(detail=True, methods=['post'])
    def test_notification(self, request, pk=None):
        """Enviar notificación de prueba a un destinatario"""
        recipient = self.get_object()
        notification_type = request.data.get('type', 'email')
        
        try:
            alert_service = AlertService()
            
            # Crear alerta de prueba
            test_alert_data = {
                'title': f'🔔 Prueba de Notificación - {recipient.name}',
                'message': f'Esta es una prueba de notificación para verificar que {recipient.name} recibe correctamente las alertas del sistema DataLens.',
                'severity': 'medium',
                'company': request.user.company
            }
            
            if notification_type in ['email', 'both']:
                if recipient.email:
                    success = alert_service.send_email_notification(
                        recipients=[recipient.email],
                        subject=test_alert_data['title'],
                        message=test_alert_data['message'],
                        alert_data=test_alert_data
                    )
                    if not success:
                        return Response({
                            'success': False,
                            'message': 'Error al enviar email de prueba'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            if notification_type in ['whatsapp', 'both']:
                if recipient.phone:
                    success = alert_service.send_whatsapp_notification(
                        phone_numbers=[recipient.phone],
                        message=test_alert_data['message'],
                        alert_data=test_alert_data
                    )
                    if not success:
                        return Response({
                            'success': False,
                            'message': 'Error al enviar WhatsApp de prueba'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': f'Notificación de prueba enviada correctamente a {recipient.name}'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al enviar notificación: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas de destinatarios"""
        recipients = self.get_queryset()
        
        stats = {
            'total': recipients.count(),
            'active': recipients.filter(is_active=True).count(),
            'inactive': recipients.filter(is_active=False).count(),
            'email_only': recipients.filter(notification_type='email').count(),
            'whatsapp_only': recipients.filter(notification_type='whatsapp').count(),
            'both': recipients.filter(notification_type='both').count(),
            'receive_all': recipients.filter(receive_all_alerts=True).count(),
            'critical_only': recipients.filter(receive_critical_only=True).count(),
            'high_and_critical': recipients.filter(receive_high_and_critical=True).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """Importar múltiples destinatarios desde un archivo"""
        import csv
        import io
        
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'message': 'No se proporcionó archivo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file_obj = request.FILES['file']
        
        try:
            # Leer archivo CSV
            decoded_file = file_obj.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(decoded_file))
            
            created_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_data, start=1):
                try:
                    # Validar campos requeridos
                    if not row.get('name'):
                        errors.append(f"Fila {row_num}: Nombre es requerido")
                        continue
                    
                    if not row.get('email') and not row.get('phone'):
                        errors.append(f"Fila {row_num}: Email o teléfono requerido")
                        continue
                    
                    # Crear destinatario
                    recipient_data = {
                        'name': row['name'],
                        'email': row.get('email', ''),
                        'phone': row.get('phone', ''),
                        'notification_type': row.get('notification_type', 'email'),
                        'receive_all_alerts': row.get('receive_all_alerts', 'true').lower() == 'true',
                        'company': request.user.company,
                        'created_by': request.user
                    }
                    
                    AlertRecipient.objects.create(**recipient_data)
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f"Fila {row_num}: {str(e)}")
            
            return Response({
                'success': True,
                'message': f'Se importaron {created_count} destinatarios correctamente',
                'created_count': created_count,
                'errors': errors
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al procesar archivo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
