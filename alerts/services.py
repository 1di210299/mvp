"""
Servicios de notificación para alertas
Incluye soporte para Email y WhatsApp
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from .models import AlertRule, Alert, NotificationLog
import requests
import logging
from datetime import timedelta, date
from decimal import Decimal

logger = logging.getLogger(__name__)


class NotificationService:
    """Servicio principal para envío de notificaciones"""
    
    def __init__(self):
        # Configurar Twilio para WhatsApp
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
            except Exception as e:
                logger.error(f"Error inicializando Twilio: {str(e)}")
    
    def send_alert_notification(self, alert, notification_type='all'):
        """
        Envía notificaciones para una alerta
        
        Args:
            alert: Instancia del modelo Alert
            notification_type: 'email', 'whatsapp' o 'all'
        """
        results = {}
        
        if notification_type in ['email', 'all']:
            results['email'] = self.send_email_notification(alert)
        
        if notification_type in ['whatsapp', 'all']:
            results['whatsapp'] = self.send_whatsapp_notification(alert)
        
        return results
    
    def send_email_notification(self, alert):
        """Envía notificación por email"""
        try:
            rule = alert.rule
            if not rule or not rule.send_email:
                return {'status': 'disabled', 'message': 'Email notifications disabled'}
            
            # Obtener destinatarios
            recipients = rule.get_recipient_emails()
            if not recipients:
                return {'status': 'error', 'message': 'No recipients found'}
            
            # Preparar contexto del email
            context = {
                'alert': alert,
                'rule': rule,
                'company': rule.company,
                'product': alert.product,
                'location': alert.location,
                'frontend_url': self._get_frontend_url(),
            }
            
            # Renderizar contenido del email
            subject = f"[DataLens] Alerta: {alert.title}"
            html_content = render_to_string('alerts/email_alert.html', context)
            text_content = render_to_string('alerts/email_alert.txt', context)
            
            # Crear y enviar email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            # Crear log de notificación
            NotificationLog.objects.create(
                alert=alert,
                notification_type='email',
                recipient=', '.join(recipients),
                subject=subject,
                content=text_content,
                status='sent',
                sent_at=timezone.now()
            )
            
            logger.info(f"Email enviado para alerta {alert.id} a {len(recipients)} destinatarios")
            return {
                'status': 'success', 
                'message': f'Email sent to {len(recipients)} recipients',
                'recipients': len(recipients)
            }
            
        except Exception as e:
            # Crear log de error
            NotificationLog.objects.create(
                alert=alert,
                notification_type='email',
                recipient='error',
                subject=f"Error sending email for alert {alert.id}",
                content=str(e),
                status='failed',
                error_message=str(e)
            )
            
            logger.error(f"Error enviando email para alerta {alert.id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def send_whatsapp_notification(self, alert):
        """Envía notificación por WhatsApp"""
        try:
            if not self.twilio_client:
                return {'status': 'disabled', 'message': 'WhatsApp not configured'}
            
            rule = alert.rule
            if not rule or not rule.send_whatsapp:
                return {'status': 'disabled', 'message': 'WhatsApp notifications disabled'}
            
            # Obtener destinatarios
            recipients = rule.get_recipient_phones()
            if not recipients:
                return {'status': 'error', 'message': 'No WhatsApp recipients found'}
            
            # Preparar mensaje para WhatsApp
            message_content = alert.get_whatsapp_message()
            
            sent_count = 0
            failed_count = 0
            
            for phone in recipients:
                try:
                    # Enviar mensaje de WhatsApp
                    message = self.twilio_client.messages.create(
                        from_=settings.TWILIO_WHATSAPP_FROM,
                        body=message_content,
                        to=f'whatsapp:{phone}'
                    )
                    
                    # Crear log de notificación exitosa
                    NotificationLog.objects.create(
                        alert=alert,
                        notification_type='whatsapp',
                        recipient=phone,
                        content=message_content,
                        status='sent',
                        sent_at=timezone.now(),
                        whatsapp_message_id=message.sid
                    )
                    
                    sent_count += 1
                    logger.info(f"WhatsApp enviado a {phone} para alerta {alert.id}")
                    
                except TwilioException as e:
                    # Crear log de error específico
                    NotificationLog.objects.create(
                        alert=alert,
                        notification_type='whatsapp',
                        recipient=phone,
                        content=message_content,
                        status='failed',
                        error_message=str(e)
                    )
                    
                    failed_count += 1
                    logger.error(f"Error enviando WhatsApp a {phone}: {str(e)}")
            
            if sent_count > 0:
                message = f'WhatsApp sent to {sent_count} recipients'
                if failed_count > 0:
                    message += f', {failed_count} failed'
                
                return {
                    'status': 'success' if failed_count == 0 else 'partial',
                    'message': message,
                    'sent': sent_count,
                    'failed': failed_count
                }
            else:
                return {
                    'status': 'error',
                    'message': f'All {failed_count} WhatsApp messages failed',
                    'failed': failed_count
                }
                
        except Exception as e:
            logger.error(f"Error general enviando WhatsApp para alerta {alert.id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def test_whatsapp_connection(self):
        """Prueba la conexión con WhatsApp"""
        try:
            if not self.twilio_client:
                return {'status': 'error', 'message': 'Twilio not configured'}
            
            # Obtener información de la cuenta
            account = self.twilio_client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
            
            return {
                'status': 'success',
                'message': 'WhatsApp connection successful',
                'account_name': account.friendly_name,
                'account_status': account.status
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def test_email_connection(self):
        """Prueba la conexión con el servidor de email"""
        try:
            from django.core.mail import get_connection
            
            connection = get_connection()
            connection.open()
            connection.close()
            
            return {
                'status': 'success',
                'message': 'Email connection successful',
                'host': settings.EMAIL_HOST,
                'port': settings.EMAIL_PORT
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _get_frontend_url(self):
        """Obtiene la URL del frontend"""
        # En desarrollo
        if settings.DEBUG:
            return 'http://localhost:8081'
        
        # En producción, obtener de variables de entorno
        return getattr(settings, 'FRONTEND_URL', 'https://your-app.netlify.app')


class AlertService:
    """Servicio principal para evaluación y generación de alertas"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def check_all_rules(self):
        """Verificar todas las reglas activas"""
        active_rules = AlertRule.objects.filter(is_active=True)
        alerts_triggered = 0
        
        for rule in active_rules:
            try:
                if self.evaluate_rule(rule):
                    alerts_triggered += 1
            except Exception as e:
                logger.error(f"Error evaluando regla {rule.id}: {str(e)}")
                continue
        
        return {
            'alerts_triggered': alerts_triggered,
            'rules_checked': active_rules.count()
        }
    
    def check_all_alerts_sync(self):
        """
        Versión síncrona de verificación de alertas para cuando Celery no está disponible
        """
        try:
            from inventory.models import Product
            from forecasting.models import DemandForecast, ReorderRecommendation
            
            logger.info("Iniciando verificación síncrona de alertas")
            
            # Obtener todas las reglas activas
            active_rules = AlertRule.objects.filter(is_active=True)
            alerts_generated = 0
            rules_processed = 0
            
            for rule in active_rules:
                try:
                    rules_processed += 1
                    
                    # Obtener productos aplicables para esta regla
                    products = self._get_applicable_products(rule)
                    
                    for product in products:
                        # Verificar diferentes tipos de alertas
                        alert_created = False
                        
                        if rule.alert_type == 'low_stock':
                            alert_created = self._check_low_stock(rule, product)
                        elif rule.alert_type == 'high_stock':
                            alert_created = self._check_high_stock(rule, product)
                        elif rule.alert_type == 'expired':
                            alert_created = self._check_expired_products(rule, product)
                        elif rule.alert_type == 'expiration':
                            alert_created = self._check_expiring_products(rule, product)
                        elif rule.alert_type == 'high_demand':
                            alert_created = self._check_high_demand(rule, product)
                        elif rule.alert_type == 'no_movement':
                            alert_created = self._check_no_movement(rule, product)
                        elif rule.alert_type == 'negative_stock':
                            alert_created = self._check_negative_stock(rule, product)
                        
                        if alert_created:
                            alerts_generated += 1
                
                except Exception as e:
                    logger.error(f"Error procesando regla {rule.id}: {str(e)}")
                    continue
            
            # Verificar alertas de predicciones
            forecasting_alerts = self._check_forecasting_alerts()
            alerts_generated += forecasting_alerts
            
            result = {
                'rules_processed': rules_processed,
                'alerts_generated': alerts_generated,
                'forecasting_alerts': forecasting_alerts,
                'execution_mode': 'synchronous',
                'timestamp': timezone.now().isoformat()
            }
            
            logger.info(f"Verificación síncrona completada: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error en verificación síncrona: {str(e)}")
            return {
                'error': str(e),
                'rules_processed': 0,
                'alerts_generated': 0,
                'execution_mode': 'synchronous'
            }
    
    def _get_applicable_products(self, rule):
        """Obtiene productos aplicables para una regla"""
        try:
            from inventory.models import Product
            
            if rule.products.exists():
                return rule.products.filter(is_active=True)
            elif rule.categories.exists():
                return Product.objects.filter(
                    category__in=rule.categories.all(),
                    is_active=True,
                    company=rule.company
                )
            else:
                return Product.objects.filter(
                    is_active=True, 
                    company=rule.company
                )[:50]  # Limitar para evitar sobrecarga
        except Exception as e:
            logger.error(f"Error obteniendo productos para regla {rule.id}: {str(e)}")
            return []
    
    def _check_low_stock(self, rule, product):
        """Verifica alerta de stock bajo"""
        try:
            current_stock = product.current_stock or 0
            
            # Determinar umbral
            if rule.threshold_value is not None:
                threshold = float(rule.threshold_value)
            elif rule.threshold_percentage and product.min_stock:
                threshold = float(product.min_stock) * (float(rule.threshold_percentage) / 100)
            else:
                threshold = float(product.min_stock or 0)
            
            if current_stock <= threshold:
                # Crear alerta de stock bajo
                alert_created = self._create_alert_if_not_exists(
                    rule=rule,
                    product=product,
                    title=f"Stock bajo: {product.name}",
                    message=f"El stock actual ({current_stock}) está por debajo del umbral ({threshold:.1f}). Stock mínimo configurado: {product.min_stock}",
                    severity='high' if current_stock <= 0 else 'medium',
                    current_value=Decimal(str(current_stock)),
                    threshold_value=Decimal(str(threshold))
                )
                
                # 🚨 NUEVA FUNCIONALIDAD: Intentar generar orden de compra automática
                if alert_created and getattr(rule, 'auto_generate_purchase_orders', False):
                    try:
                        purchase_order_generated = self.check_and_generate_purchase_orders(rule, product)
                        if purchase_order_generated:
                            logger.info(f"Orden de compra automática generada para {product.name} debido a stock bajo")
                    except Exception as e:
                        logger.error(f"Error generando orden automática para {product.name}: {str(e)}")
                
                return alert_created
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando stock bajo para {product.name}: {str(e)}")
            return False
    
    def _check_high_stock(self, rule, product):
        """Verifica alerta de stock alto"""
        try:
            current_stock = product.current_stock or 0
            
            if rule.threshold_value is not None:
                threshold = float(rule.threshold_value)
            elif rule.threshold_percentage and product.max_stock:
                threshold = float(product.max_stock) * (float(rule.threshold_percentage) / 100)
            else:
                threshold = float(product.max_stock or 100)
            
            if current_stock >= threshold and threshold > 0:
                return self._create_alert_if_not_exists(
                    rule=rule,
                    product=product,
                    title=f"Stock alto: {product.name}",
                    message=f"El stock actual ({current_stock}) supera el umbral ({threshold:.1f}). Stock máximo configurado: {product.max_stock}",
                    severity='low',
                    current_value=Decimal(str(current_stock)),
                    threshold_value=Decimal(str(threshold))
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando stock alto para {product.name}: {str(e)}")
            return False
    
    def _check_expiring_products(self, rule, product):
        """Verifica productos próximos a vencer"""
        try:
            from inventory.models import InventoryItem
            
            if not product.has_expiration:
                return False
            
            days_threshold = rule.days_before_expiration or 7
            cutoff_date = date.today() + timedelta(days=days_threshold)
            
            # Buscar items que expiran pronto
            expiring_items = InventoryItem.objects.filter(
                product=product,
                expiration_date__lte=cutoff_date,
                expiration_date__gt=date.today(),
                quantity__gt=0,
                is_active=True
            )
            
            if expiring_items.exists():
                total_expiring = sum(float(item.quantity) for item in expiring_items)
                nearest_expiry = min(item.expiration_date for item in expiring_items)
                days_until_expiry = (nearest_expiry - date.today()).days
                
                return self._create_alert_if_not_exists(
                    rule=rule,
                    product=product,
                    title=f"Producto próximo a vencer: {product.name}",
                    message=f"{total_expiring} unidades vencen en {days_until_expiry} días (fecha: {nearest_expiry})",
                    severity='high' if days_until_expiry <= 3 else 'medium',
                    current_value=Decimal(str(total_expiring)),
                    threshold_value=Decimal(str(days_threshold)),
                    context_data={
                        'expiration_date': nearest_expiry.isoformat(),
                        'days_until_expiry': days_until_expiry,
                        'expiring_batches': len(expiring_items)
                    }
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando vencimientos para {product.name}: {str(e)}")
            return False
    
    def _check_expired_products(self, rule, product):
        """Verifica productos ya vencidos"""
        try:
            from inventory.models import InventoryItem
            
            if not product.has_expiration:
                return False
            
            # Buscar items ya vencidos
            expired_items = InventoryItem.objects.filter(
                product=product,
                expiration_date__lt=date.today(),
                quantity__gt=0,
                is_active=True
            )
            
            if expired_items.exists():
                total_expired = sum(float(item.quantity) for item in expired_items)
                
                return self._create_alert_if_not_exists(
                    rule=rule,
                    product=product,
                    title=f"Producto vencido: {product.name}",
                    message=f"{total_expired} unidades han vencido y deben ser retiradas del inventario",
                    severity='critical',
                    current_value=Decimal(str(total_expired)),
                    threshold_value=Decimal('0'),
                    context_data={
                        'expired_batches': len(expired_items),
                        'action_required': 'remove_from_inventory'
                    }
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando productos vencidos para {product.name}: {str(e)}")
            return False
    
    def _check_high_demand(self, rule, product):
        """Verifica demanda alta basada en predicciones"""
        try:
            from forecasting.models import DemandForecast
            
            # Obtener pronósticos recientes (próximos 7 días)
            end_date = date.today() + timedelta(days=7)
            recent_forecasts = DemandForecast.objects.filter(
                product=product,
                forecast_date__gte=date.today(),
                forecast_date__lte=end_date
            ).order_by('forecast_date')
            
            if not recent_forecasts.exists():
                return False
            
            # Calcular demanda promedio y pico
            total_demand = sum(float(f.predicted_demand) for f in recent_forecasts)
            avg_daily_demand = total_demand / len(recent_forecasts)
            peak_demand = max(float(f.predicted_demand) for f in recent_forecasts)
            
            # Determinar umbral
            if rule.threshold_value is not None:
                threshold = float(rule.threshold_value)
            else:
                # Usar 150% del stock actual como umbral por defecto
                threshold = float(product.current_stock or 0) * 1.5
            
            if peak_demand > threshold:
                current_stock = product.current_stock or 0
                days_of_coverage = current_stock / avg_daily_demand if avg_daily_demand > 0 else 0
                
                return self._create_alert_if_not_exists(
                    rule=rule,
                    product=product,
                    title=f"Demanda alta proyectada: {product.name}",
                    message=f"Se proyecta una demanda pico de {peak_demand:.1f} unidades. Stock actual: {current_stock} ({days_of_coverage:.1f} días de cobertura)",
                    severity='medium',
                    current_value=Decimal(str(peak_demand)),
                    threshold_value=Decimal(str(threshold)),
                    context_data={
                        'avg_daily_demand': avg_daily_demand,
                        'days_of_coverage': days_of_coverage,
                        'forecast_period': f"{date.today()} to {end_date}"
                    }
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando demanda alta para {product.name}: {str(e)}")
            return False
    
    def _check_no_movement(self, rule, product):
        """Verifica productos sin movimiento"""
        try:
            from inventory.models import Transaction
            
            days_threshold = rule.threshold_value or 30
            cutoff_date = timezone.now() - timedelta(days=int(days_threshold))
            
            # Buscar transacciones recientes - FILTRAR las que no tienen transaction_date
            recent_transactions = Transaction.objects.filter(
                product=product,
                transaction_date__isnull=False,  # ✅ NUEVA LÍNEA - Excluir transacciones sin fecha
                transaction_date__gte=cutoff_date
            ).exists()
            
            current_stock = product.current_stock or 0
            
            if not recent_transactions and current_stock > 0:
                # Formatear la fecha correctamente para el contexto
                cutoff_date_str = cutoff_date.isoformat() if cutoff_date else None
                
                return self._create_alert_if_not_exists(
                    rule=rule,
                    product=product,
                    title=f"Sin movimiento: {product.name}",
                    message=f"No ha habido movimientos en {days_threshold} días. Stock actual: {current_stock}",
                    severity='low',
                    current_value=Decimal(str(days_threshold)),
                    threshold_value=Decimal(str(days_threshold)),
                    context_data={
                        'current_stock': current_stock,
                        'last_check_date': cutoff_date_str
                    }
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando sin movimiento para {product.name}: {str(e)}")
            return False
    
    def _check_negative_stock(self, rule, product):
        """Verifica stock negativo"""
        try:
            current_stock = product.current_stock or 0
            
            if current_stock < 0:
                return self._create_alert_if_not_exists(
                    rule=rule,
                    product=product,
                    title=f"Stock negativo: {product.name}",
                    message=f"El stock actual es negativo ({current_stock}). Se requiere ajuste inmediato",
                    severity='critical',
                    current_value=Decimal(str(current_stock)),
                    threshold_value=Decimal('0'),
                    context_data={
                        'action_required': 'stock_adjustment'
                    }
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando stock negativo para {product.name}: {str(e)}")
            return False
    
    def _check_forecasting_alerts(self):
        """Verifica alertas basadas en predicciones y recomendaciones"""
        try:
            from forecasting.models import ReorderRecommendation
            alerts_created = 0
            
            # Obtener recomendaciones urgentes
            urgent_recommendations = ReorderRecommendation.objects.filter(
                status='pending',
                priority__in=['urgent', 'high'],
                recommended_order_date__lte=date.today() + timedelta(days=3)
            ).select_related('product')
            
            for rec in urgent_recommendations:
                # Crear alerta automática para recomendaciones urgentes
                alert_created = self._create_alert_if_not_exists(
                    rule=None,  # Alerta automática del sistema
                    product=rec.product,
                    title=f"Recomendación de reorden urgente: {rec.product.name}",
                    message=f"Se recomienda ordenar {rec.recommended_quantity} unidades. Stock actual: {rec.current_stock}. Fecha recomendada: {rec.recommended_order_date}",
                    severity='high' if rec.priority == 'urgent' else 'medium',
                    current_value=rec.current_stock,
                    threshold_value=rec.recommended_quantity,
                    context_data={
                        'recommendation_id': rec.id,
                        'expected_stockout': rec.expected_stockout_date.isoformat() if rec.expected_stockout_date else None,
                        'lead_time_days': rec.lead_time_days,
                        'estimated_cost': float(rec.estimated_cost)
                    }
                )
                if alert_created:
                    alerts_created += 1
            
            return alerts_created
            
        except Exception as e:
            logger.error(f"Error verificando alertas de forecasting: {str(e)}")
            return 0
    
    def _create_alert_if_not_exists(self, rule, product, title, message, severity, 
                                  current_value, threshold_value, context_data=None):
        """Crear alerta si no existe una reciente para evitar duplicados"""
        try:
            recent_cutoff = timezone.now() - timedelta(hours=24)
            
            # Buscar alerta similar reciente - FILTRAR las que tienen created_at None
            similar_alert = Alert.objects.filter(
                product=product,
                status__in=['active', 'acknowledged'],
                created_at__isnull=False,  # ✅ Excluir alertas sin fecha de creación
                created_at__gte=recent_cutoff
            )
            
            if rule:
                similar_alert = similar_alert.filter(rule=rule)
            else:
                # Para alertas automáticas, verificar por título similar
                similar_alert = similar_alert.filter(title__icontains=title.split(':')[0])
            
            if similar_alert.exists():
                return False
            
            # Crear nueva alerta
            alert = Alert.objects.create(
                company=product.company,
                rule=rule,
                product=product,
                title=title,
                message=message,
                severity=severity,
                current_value=current_value,
                threshold_value=threshold_value,
                context_data=context_data or {},
                status='active'
            )
            
            # Enviar notificaciones inmediatamente si está configurado
            if rule and rule.frequency == 'immediate':
                self.notification_service.send_alert_notification(alert)
            elif not rule:  # Alertas automáticas del sistema
                self.notification_service.send_alert_notification(alert)
            
            logger.info(f"Alerta creada: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando alerta para {product.name}: {str(e)}")
            return False
    
    def evaluate_rule(self, rule):
        """Evaluar una regla específica"""
        try:
            products = self._get_applicable_products(rule)
            alerts_created = False
            
            for product in products:
                if rule.alert_type == 'low_stock':
                    if self._check_low_stock(rule, product):
                        alerts_created = True
                elif rule.alert_type == 'high_stock':
                    if self._check_high_stock(rule, product):
                        alerts_created = True
                elif rule.alert_type == 'expiration':
                    if self._check_expiring_products(rule, product):
                        alerts_created = True
                elif rule.alert_type == 'expired':
                    if self._check_expired_products(rule, product):
                        alerts_created = True
                elif rule.alert_type == 'high_demand':
                    if self._check_high_demand(rule, product):
                        alerts_created = True
                elif rule.alert_type == 'no_movement':
                    if self._check_no_movement(rule, product):
                        alerts_created = True
                elif rule.alert_type == 'negative_stock':
                    if self._check_negative_stock(rule, product):
                        alerts_created = True
            
            return alerts_created
            
        except Exception as e:
            logger.error(f"Error evaluando regla {rule.id}: {str(e)}")
            return False
    
    def create_alert(self, rule):
        """Crear una alerta básica (mantenido por compatibilidad)"""
        try:
            alert = Alert.objects.create(
                company=rule.company,
                rule=rule,
                title=f"Alerta: {rule.name}",
                message=f"La regla {rule.name} ha sido activada",
                severity='medium',
                status='active'
            )
            
            # Enviar notificaciones
            self.notification_service.send_alert_notification(alert)
            
            return alert
        except Exception as e:
            logger.error(f"Error creando alerta para regla {rule.id}: {str(e)}")
            return None
    
    def test_rule(self, rule):
        """Simular evaluación de regla para testing"""
        try:
            products = self._get_applicable_products(rule)
            
            return {
                'rule_valid': True,
                'products_count': len(products),
                'would_trigger': len(products) > 0,
                'test_timestamp': timezone.now().isoformat(),
                'rule_type': rule.alert_type
            }
        except Exception as e:
            return {
                'rule_valid': False,
                'error': str(e),
                'test_timestamp': timezone.now().isoformat()
            }
    
    def check_and_generate_purchase_orders(self, rule, product):
        """
        🚨 NUEVA FUNCIONALIDAD: Verificar si se debe generar orden de compra automática
        """
        try:
            # Solo para alertas de stock bajo
            if rule.alert_type != 'low_stock':
                return False
            
            # Verificar configuración de órdenes automáticas
            if not getattr(rule, 'auto_generate_purchase_orders', False):
                return False
            
            # Importar servicio de órdenes (lazy import para evitar dependencias circulares)
            from inventory.services.purchase_order_service import PurchaseOrderService
            
            purchase_service = PurchaseOrderService()
            
            # Verificar si ya existe una orden pendiente reciente
            if purchase_service._has_pending_order(product):
                logger.info(f"Producto {product.name} ya tiene orden pendiente, saltando")
                return False
            
            # Calcular cantidad a ordenar
            quantity_to_order = purchase_service._calculate_order_quantity(product)
            
            if quantity_to_order <= 0:
                return False
            
            # Generar orden de compra
            purchase_order = purchase_service._create_purchase_order(product, quantity_to_order)
            
            if purchase_order:
                # Enviar email automáticamente si está configurado
                if purchase_service._should_send_email_automatically(purchase_order):
                    email_sent = purchase_service._send_purchase_order_email(purchase_order)
                    
                    if email_sent:
                        logger.info(f"Email de orden automática enviado: {purchase_order.order_number}")
                
                # Crear alerta de seguimiento
                self._create_purchase_order_alert(purchase_order)
                
                logger.info(f"Orden automática generada: {purchase_order.order_number} para {product.name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error generando orden automática para {product.name}: {str(e)}")
            return False
    
    def check_and_generate_purchase_orders(self, rule, product):
        """
        Verificar si un producto necesita orden de compra automática
        Integra el AlertService con el PurchaseOrderService
        """
        try:
            # Verificar si la regla tiene habilitadas las órdenes automáticas
            if not getattr(rule, 'auto_generate_purchase_orders', False):
                return False
            
            # Solo generar para alertas de stock bajo
            if rule.alert_type != 'low_stock':
                return False
            
            # Verificar si ya existe una orden pendiente reciente
            from inventory.models import PurchaseOrder
            recent_order_exists = PurchaseOrder.objects.filter(
                product=product,
                status__in=['draft', 'sent', 'confirmed'],
                created_at__gte=timezone.now() - timedelta(days=7)
            ).exists()
            
            if recent_order_exists:
                logger.info(f"Ya existe orden reciente para {product.name}, omitiendo")
                return False
            
            # Usar el servicio de órdenes de compra para generar automáticamente
            from inventory.services.purchase_order_service import PurchaseOrderService
            
            purchase_service = PurchaseOrderService()
            
            # Calcular cantidad necesaria
            current_stock = product.current_stock or 0
            min_stock = product.min_stock or 10
            max_stock = product.max_stock or (min_stock * 3)
            
            # Cantidad básica para llevar al máximo
            quantity_needed = max(max_stock - current_stock, min_stock)
            
            if quantity_needed <= 0:
                return False
            
            # Crear la orden de compra
            purchase_order = purchase_service._create_purchase_order(product, quantity_needed)
            
            if purchase_order:
                # Intentar enviar email automáticamente
                if purchase_service._should_send_email_automatically(purchase_order):
                    email_sent = purchase_service._send_purchase_order_email(purchase_order)
                    logger.info(f"Email {'enviado' if email_sent else 'falló'} para orden {purchase_order.order_number}")
                
                # Crear alerta de seguimiento
                self._create_purchase_order_alert(purchase_order)
                
                logger.info(f"Orden automática generada: {purchase_order.order_number} para {product.name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error generando orden automática para {product.name}: {str(e)}")
            return False
    
    def _create_purchase_order_alert(self, purchase_order):
        """Crear alerta de seguimiento para orden de compra generada"""
        try:
            Alert.objects.create(
                company=purchase_order.company,
                product=purchase_order.product,
                title=f"✅ Orden de Compra Generada: {purchase_order.product.name}",
                message=f"Se ha generado automáticamente la orden {purchase_order.order_number} "
                       f"para reabastecer {purchase_order.quantity} unidades. "
                       f"{'Email enviado al proveedor.' if purchase_order.email_sent else 'Pendiente envío de email.'}",
                severity='low',  # Baja porque es informativa
                status='active',
                source='system',
                current_value=purchase_order.quantity,
                threshold_value=purchase_order.product.min_stock,
                context_data={
                    'purchase_order_id': purchase_order.id,
                    'order_number': purchase_order.order_number,
                    'auto_generated': True,
                    'email_sent': purchase_order.email_sent,
                    'supplier_email': purchase_order.supplier_email
                }
            )
            
        except Exception as e:
            logger.error(f"Error creando alerta de orden {purchase_order.order_number}: {str(e)}")


# Crear instancia global del servicio de notificaciones
notification_service = NotificationService()