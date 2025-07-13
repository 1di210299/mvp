"""
Tareas asíncronas para el módulo de alertas
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .models import AlertRule, Alert, NotificationLog
from .services import notification_service
from inventory.models import Product, Transaction, Location
from authentication.models import User, Company
from django.db import models

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_all_alerts(self):
    """
    Tarea principal para verificar todas las reglas de alerta activas
    Se ejecuta cada hora según la configuración de Celery Beat
    """
    try:
        logger.info("Iniciando verificación de alertas")
        
        # Obtener todas las reglas activas
        active_rules = AlertRule.objects.filter(is_active=True)
        alerts_generated = 0
        
        for rule in active_rules:
            try:
                result = check_alert_rule.delay(rule.id)
                alerts_generated += 1
            except Exception as e:
                logger.error(f"Error al procesar regla {rule.id}: {str(e)}")
        
        logger.info(f"Verificación completada. {alerts_generated} reglas procesadas")
        return f"Processed {alerts_generated} alert rules"
        
    except Exception as exc:
        logger.error(f"Error en check_all_alerts: {str(exc)}")
        self.retry(countdown=60 * 5, exc=exc)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def check_alert_rule(self, rule_id):
    """
    Verifica una regla de alerta específica
    """
    try:
        rule = AlertRule.objects.get(id=rule_id, is_active=True)
        logger.info(f"Verificando regla: {rule.name}")
        
        # Obtener productos aplicables
        products = get_applicable_products(rule)
        alerts_created = 0
        
        for product in products:
            locations = get_applicable_locations(rule, product)
            
            for location in locations:
                alert_triggered = False
                
                # Verificar según el tipo de alerta
                if rule.alert_type == 'low_stock':
                    alert_triggered = check_low_stock_alert(rule, product, location)
                elif rule.alert_type == 'high_stock':
                    alert_triggered = check_high_stock_alert(rule, product, location)
                elif rule.alert_type == 'expiration':
                    alert_triggered = check_expiration_alert(rule, product, location)
                elif rule.alert_type == 'expired':
                    alert_triggered = check_expired_alert(rule, product, location)
                elif rule.alert_type == 'high_demand':
                    alert_triggered = check_high_demand_alert(rule, product, location)
                elif rule.alert_type == 'no_movement':
                    alert_triggered = check_no_movement_alert(rule, product, location)
                elif rule.alert_type == 'negative_stock':
                    alert_triggered = check_negative_stock_alert(rule, product, location)
                
                if alert_triggered:
                    alerts_created += 1
        
        logger.info(f"Regla {rule.name}: {alerts_created} alertas generadas")
        return f"Rule {rule.name}: {alerts_created} alerts generated"
        
    except AlertRule.DoesNotExist:
        logger.warning(f"Regla de alerta {rule_id} no encontrada")
        return f"Alert rule {rule_id} not found"
    except Exception as exc:
        logger.error(f"Error en check_alert_rule {rule_id}: {str(exc)}")
        self.retry(countdown=60 * 2, exc=exc)


@shared_task(bind=True, max_retries=3)
def send_alert_notification(self, alert_id, notification_type='all'):
    """
    Envía notificaciones para una alerta específica usando el servicio mejorado
    """
    try:
        alert = Alert.objects.get(id=alert_id)
        logger.info(f"Enviando notificaciones para alerta {alert_id}")
        
        # Usar el servicio de notificaciones mejorado
        results = notification_service.send_alert_notification(alert, notification_type)
        
        # Log de resultados
        for ntype, result in results.items():
            if result['status'] == 'success':
                logger.info(f"Notificación {ntype} enviada exitosamente para alerta {alert_id}")
            elif result['status'] == 'partial':
                logger.warning(f"Notificación {ntype} enviada parcialmente para alerta {alert_id}: {result['message']}")
            elif result['status'] == 'disabled':
                logger.info(f"Notificación {ntype} deshabilitada para alerta {alert_id}")
            else:
                logger.error(f"Error en notificación {ntype} para alerta {alert_id}: {result['message']}")
        
        return results
        
    except Alert.DoesNotExist:
        logger.warning(f"Alerta {alert_id} no encontrada")
        return {"error": f"Alert {alert_id} not found"}
    except Exception as exc:
        logger.error(f"Error enviando notificaciones {alert_id}: {str(exc)}")
        self.retry(countdown=60 * 2, exc=exc)


@shared_task(bind=True, max_retries=3)
def send_whatsapp_notification(self, alert_id):
    """
    Envía notificación por WhatsApp específicamente
    """
    try:
        alert = Alert.objects.get(id=alert_id)
        result = notification_service.send_whatsapp_notification(alert)
        
        logger.info(f"WhatsApp notification result for alert {alert_id}: {result}")
        return result
        
    except Alert.DoesNotExist:
        logger.warning(f"Alerta {alert_id} no encontrada para WhatsApp")
        return {"error": f"Alert {alert_id} not found"}
    except Exception as exc:
        logger.error(f"Error enviando WhatsApp {alert_id}: {str(exc)}")
        self.retry(countdown=60 * 2, exc=exc)


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, alert_id):
    """
    Envía notificación por email específicamente
    """
    try:
        alert = Alert.objects.get(id=alert_id)
        result = notification_service.send_email_notification(alert)
        
        logger.info(f"Email notification result for alert {alert_id}: {result}")
        return result
        
    except Alert.DoesNotExist:
        logger.warning(f"Alerta {alert_id} no encontrada para email")
        return {"error": f"Alert {alert_id} not found"}
    except Exception as exc:
        logger.error(f"Error enviando email {alert_id}: {str(exc)}")
        self.retry(countdown=60 * 2, exc=exc)


@shared_task
def test_notification_services():
    """
    Tarea para probar los servicios de notificación
    """
    try:
        results = {}
        
        # Probar email
        email_test = notification_service.test_email_connection()
        results['email'] = email_test
        
        # Probar WhatsApp
        whatsapp_test = notification_service.test_whatsapp_connection()
        results['whatsapp'] = whatsapp_test
        
        logger.info(f"Test notification services results: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error testing notification services: {str(e)}")
        return {"error": str(e)}


@shared_task
def cleanup_old_alerts():
    """
    Limpia alertas antigas y resueltas
    """
    try:
        # Eliminar alertas resueltas más antiguas de 30 días
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = Alert.objects.filter(
            status='resolved',
            created_at__lt=cutoff_date
        ).delete()[0]
        
        # Limpiar logs de notificación más antiguos de 60 días
        log_cutoff_date = timezone.now() - timedelta(days=60)
        deleted_logs = NotificationLog.objects.filter(
            created_at__lt=log_cutoff_date
        ).delete()[0]
        
        logger.info(f"Eliminadas {deleted_count} alertas antigas y {deleted_logs} logs de notificación")
        return f"Cleaned up {deleted_count} old alerts and {deleted_logs} notification logs"
        
    except Exception as e:
        logger.error(f"Error en cleanup_old_alerts: {str(e)}")
        return f"Error: {str(e)}"


def get_applicable_products(rule):
    """Obtiene los productos aplicables para una regla"""
    if rule.products.exists():
        return rule.products.filter(is_active=True)
    elif rule.categories.exists():
        return Product.objects.filter(
            category__in=rule.categories.all(),
            is_active=True,
            company=rule.company
        )
    else:
        return Product.objects.filter(is_active=True, company=rule.company)


def get_applicable_locations(rule, product):
    """Obtiene las ubicaciones aplicables para una regla y producto"""
    if rule.locations.exists():
        return rule.locations.filter(is_active=True)
    else:
        return Location.objects.filter(is_active=True, company=rule.company)


def check_low_stock_alert(rule, product, location):
    """Verifica alerta de stock bajo"""
    try:
        # Obtener stock actual
        current_stock = product.current_stock
        
        # Determinar umbral
        if rule.threshold_value:
            threshold = rule.threshold_value
        elif rule.threshold_percentage and product.min_stock:
            threshold = product.min_stock * (rule.threshold_percentage / 100)
        else:
            threshold = product.min_stock or 0
        
        if current_stock <= threshold:
            return create_alert(
                rule=rule,
                product=product,
                location=location,
                title=f"Stock bajo: {product.name}",
                description=f"El stock actual ({current_stock}) está por debajo del umbral ({threshold})",
                current_value=current_stock,
                threshold_value=threshold,
                severity='medium' if current_stock > 0 else 'high'
            )
        
        return False
        
    except Exception as e:
        logger.error(f"Error verificando stock bajo para {product.name}: {str(e)}")
        return False


def check_high_stock_alert(rule, product, location):
    """Verifica alerta de stock alto"""
    try:
        current_stock = product.current_stock
        
        if rule.threshold_value:
            threshold = rule.threshold_value
        elif rule.threshold_percentage and product.max_stock:
            threshold = product.max_stock * (rule.threshold_percentage / 100)
        else:
            threshold = product.max_stock or float('inf')
        
        if current_stock >= threshold:
            return create_alert(
                rule=rule,
                product=product,
                location=location,
                title=f"Stock alto: {product.name}",
                description=f"El stock actual ({current_stock}) supera el umbral ({threshold})",
                current_value=current_stock,
                threshold_value=threshold,
                severity='low'
            )
        
        return False
        
    except Exception as e:
        logger.error(f"Error verificando stock alto para {product.name}: {str(e)}")
        return False


def check_expiration_alert(rule, product, location):
    """Verifica alerta de próximo vencimiento"""
    try:
        if not rule.days_before_expiration:
            return False
        
        from inventory.models import InventoryItem
        
        cutoff_date = timezone.now().date() + timedelta(days=rule.days_before_expiration)
        
        expiring_items = InventoryItem.objects.filter(
            product=product,
            location=location,
            expiration_date__lte=cutoff_date,
            expiration_date__gt=timezone.now().date(),
            quantity__gt=0,
            is_active=True
        )
        
        if expiring_items.exists():
            total_quantity = sum(item.quantity for item in expiring_items)
            return create_alert(
                rule=rule,
                product=product,
                location=location,
                title=f"Próximo a vencer: {product.name}",
                description=f"{total_quantity} unidades vencen en los próximos {rule.days_before_expiration} días",
                current_value=total_quantity,
                threshold_value=rule.days_before_expiration,
                severity='medium'
            )
        
        return False
        
    except Exception as e:
        logger.error(f"Error verificando vencimiento para {product.name}: {str(e)}")
        return False


def check_expired_alert(rule, product, location):
    """Verifica alerta de productos vencidos"""
    try:
        from inventory.models import InventoryItem
        
        expired_items = InventoryItem.objects.filter(
            product=product,
            location=location,
            expiration_date__lt=timezone.now().date(),
            quantity__gt=0,
            is_active=True
        )
        
        if expired_items.exists():
            total_quantity = sum(item.quantity for item in expired_items)
            return create_alert(
                rule=rule,
                product=product,
                location=location,
                title=f"Producto vencido: {product.name}",
                description=f"{total_quantity} unidades han vencido",
                current_value=total_quantity,
                threshold_value=0,
                severity='high'
            )
        
        return False
        
    except Exception as e:
        logger.error(f"Error verificando productos vencidos para {product.name}: {str(e)}")
        return False


def check_negative_stock_alert(rule, product, location):
    """Verifica alerta de stock negativo"""
    try:
        current_stock = product.current_stock
        
        if current_stock < 0:
            return create_alert(
                rule=rule,
                product=product,
                location=location,
                title=f"Stock negativo: {product.name}",
                description=f"El stock actual es negativo: {current_stock}",
                current_value=current_stock,
                threshold_value=0,
                severity='critical'
            )
        
        return False
        
    except Exception as e:
        logger.error(f"Error verificando stock negativo para {product.name}: {str(e)}")
        return False


def check_high_demand_alert(rule, product, location):
    """Verifica alerta de demanda alta"""
    try:
        # Calcular demanda de los últimos 7 días
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        recent_demand = Transaction.objects.filter(
            product=product,
            location=location,
            transaction_type='sale',
            transaction_date__isnull=False,  # ✅ NUEVA LÍNEA - Excluir transacciones sin fecha
            transaction_date__date__range=[start_date, end_date]
        ).aggregate(
            total_demand=models.Sum('quantity')
        )['total_demand'] or 0
        
        # Calcular demanda promedio histórica
        historical_start = end_date - timedelta(days=90)
        avg_demand = Transaction.objects.filter(
            product=product,
            location=location,
            transaction_type='sale',
            transaction_date__isnull=False,  # ✅ NUEVA LÍNEA - Excluir transacciones sin fecha
            transaction_date__date__range=[historical_start, start_date]
        ).aggregate(
            avg_demand=models.Avg('quantity')
        )['avg_demand'] or 0
        
        threshold_multiplier = rule.threshold_percentage / 100 if rule.threshold_percentage else 2.0
        threshold = avg_demand * threshold_multiplier * 7  # Para 7 días
        
        if recent_demand > threshold:
            return create_alert(
                rule=rule,
                product=product,
                location=location,
                title=f"Demanda alta: {product.name}",
                description=f"Demanda reciente ({recent_demand}) supera el umbral ({threshold:.2f})",
                current_value=recent_demand,
                threshold_value=threshold,
                severity='medium'
            )
        
        return False
        
    except Exception as e:
        logger.error(f"Error verificando demanda alta para {product.name}: {str(e)}")
        return False


def check_no_movement_alert(rule, product, location):
    """Verifica alerta de productos sin movimiento"""
    try:
        days_threshold = rule.threshold_value or 30
        cutoff_date = timezone.now().date() - timedelta(days=int(days_threshold))
        
        recent_transactions = Transaction.objects.filter(
            product=product,
            location=location,
            transaction_date__isnull=False,  # ✅ NUEVA LÍNEA - Excluir transacciones sin fecha
            transaction_date__date__gte=cutoff_date
        ).exists()
        
        if not recent_transactions:
            return create_alert(
                rule=rule,
                product=product,
                location=location,
                title=f"Sin movimiento: {product.name}",
                description=f"No hay movimientos en los últimos {days_threshold} días",
                current_value=days_threshold,
                threshold_value=days_threshold,
                severity='low'
            )
        
        return False
        
    except Exception as e:
        logger.error(f"Error verificando sin movimiento para {product.name}: {str(e)}")
        return False


def create_alert(rule, product, location, title, description, current_value, threshold_value, severity):
    """Crea una nueva alerta si no existe una similar reciente"""
    try:
        # Verificar si ya existe una alerta similar en las últimas 24 horas
        recent_cutoff = timezone.now() - timedelta(hours=24)
        existing_alert = Alert.objects.filter(
            rule=rule,
            product=product,
            location=location,
            status__in=['active', 'acknowledged'],
            created_at__gte=recent_cutoff
        ).first()
        
        if existing_alert:
            # Actualizar alerta existente
            existing_alert.current_value = current_value
            existing_alert.threshold_value = threshold_value
            existing_alert.save()
            return False
        
        # Crear nueva alerta
        alert = Alert.objects.create(
            company=rule.company,
            rule=rule,
            product=product,
            location=location,
            title=title,
            message=description,
            severity=severity,
            current_value=current_value,
            threshold_value=threshold_value,
            status='active'
        )
        
        # Programar envío de notificación si está habilitado
        if rule.frequency == 'immediate':
            # Enviar notificaciones inmediatamente
            send_alert_notification.delay(alert.id)
        
        logger.info(f"Alerta creada: {title}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando alerta: {str(e)}")
        return False
