"""
Signals para detectar cambios automáticamente y generar alertas
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import logging

from .models import AlertRule, Alert
from .services import AlertService, notification_service

logger = logging.getLogger(__name__)
alert_service = AlertService()

@receiver(post_save, sender='inventory.Product')
def check_product_alerts(sender, instance, created, **kwargs):
    """
    Se ejecuta automáticamente cuando se guarda un producto
    Verifica si debe generar alertas de stock bajo/alto
    """
    try:
        logger.info(f"🔍 Verificando alertas para producto: {instance.name}")
        
        # Obtener reglas activas para esta empresa
        rules = AlertRule.objects.filter(
            company=instance.company,
            is_active=True
        )
        
        for rule in rules:
            # Solo verificar reglas aplicables a este producto
            if _is_rule_applicable_to_product(rule, instance):
                _check_product_rule(rule, instance)
                
    except Exception as e:
        logger.error(f"Error en signal de producto {instance.id}: {str(e)}")

@receiver(post_save, sender='inventory.InventoryItem')
def check_inventory_alerts(sender, instance, created, **kwargs):
    """
    Se ejecuta automáticamente cuando cambia el inventario
    Verifica alertas de stock, vencimiento, etc.
    """
    try:
        product = instance.product
        logger.info(f"📦 Verificando alertas de inventario para: {product.name}")
        
        # Obtener reglas activas
        rules = AlertRule.objects.filter(
            company=product.company,
            is_active=True
        )
        
        for rule in rules:
            if _is_rule_applicable_to_product(rule, product):
                _check_inventory_rule(rule, product, instance)
                
    except Exception as e:
        logger.error(f"Error en signal de inventario {instance.id}: {str(e)}")

@receiver(post_save, sender='inventory.Transaction')
def check_transaction_alerts(sender, instance, created, **kwargs):
    """
    Se ejecuta automáticamente cuando hay una transacción
    Verifica alertas de demanda alta, movimientos, etc.
    """
    if not created:
        return  # Solo procesar transacciones nuevas
        
    try:
        product = instance.product
        logger.info(f"💰 Verificando alertas de transacción para: {product.name}")
        
        # Obtener reglas activas relacionadas con transacciones
        rules = AlertRule.objects.filter(
            company=product.company,
            is_active=True,
            alert_type__in=['high_demand', 'no_movement']
        )
        
        for rule in rules:
            if _is_rule_applicable_to_product(rule, product):
                _check_transaction_rule(rule, product, instance)
                
    except Exception as e:
        logger.error(f"Error en signal de transacción {instance.id}: {str(e)}")

def _is_rule_applicable_to_product(rule, product):
    """Verifica si una regla aplica a un producto específico"""
    try:
        # Si la regla tiene productos específicos
        if rule.products.exists():
            return rule.products.filter(id=product.id).exists()
        
        # Si la regla tiene categorías específicas
        if rule.categories.exists():
            return rule.categories.filter(id=product.category_id).exists()
        
        # Si no tiene filtros, aplica a todos los productos de la empresa
        return True
        
    except Exception as e:
        logger.error(f"Error verificando aplicabilidad de regla {rule.id} a producto {product.id}: {str(e)}")
        return False

def _check_product_rule(rule, product):
    """Verifica reglas específicas de producto"""
    try:
        current_stock = product.current_stock
        
        if rule.alert_type == 'low_stock':
            _check_low_stock_rule(rule, product, current_stock)
        elif rule.alert_type == 'high_stock':
            _check_high_stock_rule(rule, product, current_stock)
        elif rule.alert_type == 'negative_stock':
            _check_negative_stock_rule(rule, product, current_stock)
            
    except Exception as e:
        logger.error(f"Error verificando regla de producto {rule.id}: {str(e)}")

def _check_inventory_rule(rule, product, inventory_item):
    """Verifica reglas específicas de inventario"""
    try:
        if rule.alert_type == 'expiration':
            _check_expiration_rule(rule, product, inventory_item)
        elif rule.alert_type == 'expired':
            _check_expired_rule(rule, product, inventory_item)
            
    except Exception as e:
        logger.error(f"Error verificando regla de inventario {rule.id}: {str(e)}")

def _check_transaction_rule(rule, product, transaction):
    """Verifica reglas específicas de transacciones"""
    try:
        if rule.alert_type == 'high_demand':
            _check_high_demand_rule(rule, product)
        elif rule.alert_type == 'no_movement':
            _check_no_movement_rule(rule, product)
            
    except Exception as e:
        logger.error(f"Error verificando regla de transacción {rule.id}: {str(e)}")

def _check_low_stock_rule(rule, product, current_stock):
    """Verifica regla de stock bajo"""
    try:
        # Determinar umbral
        if rule.threshold_value:
            threshold = rule.threshold_value
        elif rule.threshold_percentage and product.min_stock:
            threshold = product.min_stock * (rule.threshold_percentage / 100)
        else:
            threshold = product.min_stock or 0
        
        if current_stock <= threshold:
            _create_alert_if_not_exists(
                rule=rule,
                product=product,
                title=f"🔴 Stock bajo: {product.name}",
                message=f"El stock actual ({current_stock}) está por debajo del umbral ({threshold})",
                severity='medium' if current_stock > 0 else 'high',
                current_value=current_stock,
                threshold_value=threshold
            )
            
    except Exception as e:
        logger.error(f"Error verificando stock bajo: {str(e)}")

def _check_high_stock_rule(rule, product, current_stock):
    """Verifica regla de stock alto"""
    try:
        if rule.threshold_value:
            threshold = rule.threshold_value
        elif rule.threshold_percentage and product.max_stock:
            threshold = product.max_stock * (rule.threshold_percentage / 100)
        else:
            threshold = product.max_stock or float('inf')
        
        if current_stock >= threshold and threshold != float('inf'):
            _create_alert_if_not_exists(
                rule=rule,
                product=product,
                title=f"🔵 Stock alto: {product.name}",
                message=f"El stock actual ({current_stock}) supera el umbral ({threshold})",
                severity='low',
                current_value=current_stock,
                threshold_value=threshold
            )
            
    except Exception as e:
        logger.error(f"Error verificando stock alto: {str(e)}")

def _check_negative_stock_rule(rule, product, current_stock):
    """Verifica regla de stock negativo"""
    try:
        if current_stock < 0:
            _create_alert_if_not_exists(
                rule=rule,
                product=product,
                title=f"⚠️ Stock negativo: {product.name}",
                message=f"El stock actual es negativo: {current_stock}",
                severity='critical',
                current_value=current_stock,
                threshold_value=0
            )
            
    except Exception as e:
        logger.error(f"Error verificando stock negativo: {str(e)}")

def _check_expiration_rule(rule, product, inventory_item):
    """Verifica regla de vencimiento próximo"""
    try:
        if not rule.days_before_expiration or not inventory_item.expiration_date:
            return
            
        days_until_expiration = (inventory_item.expiration_date - timezone.now().date()).days
        
        if days_until_expiration <= rule.days_before_expiration and days_until_expiration > 0:
            _create_alert_if_not_exists(
                rule=rule,
                product=product,
                title=f"🕒 Próximo a vencer: {product.name}",
                message=f"El producto vence en {days_until_expiration} días (cantidad: {inventory_item.quantity})",
                severity='medium',
                current_value=days_until_expiration,
                threshold_value=rule.days_before_expiration
            )
            
    except Exception as e:
        logger.error(f"Error verificando vencimiento: {str(e)}")

def _check_expired_rule(rule, product, inventory_item):
    """Verifica regla de productos vencidos"""
    try:
        if inventory_item.expiration_date and inventory_item.expiration_date < timezone.now().date():
            _create_alert_if_not_exists(
                rule=rule,
                product=product,
                title=f"❌ Producto vencido: {product.name}",
                message=f"El producto venció el {inventory_item.expiration_date} (cantidad: {inventory_item.quantity})",
                severity='high',
                current_value=0,
                threshold_value=0
            )
            
    except Exception as e:
        logger.error(f"Error verificando producto vencido: {str(e)}")

def _check_high_demand_rule(rule, product):
    """Verifica regla de demanda alta (simplificada)"""
    try:
        from inventory.models import Transaction
        from django.db.models import Sum
        
        # Calcular demanda de los últimos 7 días
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        recent_demand = Transaction.objects.filter(
            product=product,
            transaction_type='sale',
            transaction_date__date__range=[start_date, end_date]
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Umbral simple (se puede mejorar)
        threshold = rule.threshold_value or 50
        
        if recent_demand > threshold:
            _create_alert_if_not_exists(
                rule=rule,
                product=product,
                title=f"📈 Alta demanda: {product.name}",
                message=f"Demanda reciente ({recent_demand}) supera el umbral ({threshold})",
                severity='medium',
                current_value=recent_demand,
                threshold_value=threshold
            )
            
    except Exception as e:
        logger.error(f"Error verificando demanda alta: {str(e)}")

def _check_no_movement_rule(rule, product):
    """Verifica regla de productos sin movimiento"""
    try:
        from inventory.models import Transaction
        
        days_threshold = rule.threshold_value or 30
        cutoff_date = timezone.now().date() - timedelta(days=int(days_threshold))
        
        recent_transactions = Transaction.objects.filter(
            product=product,
            transaction_date__isnull=False,  # ✅ NUEVA LÍNEA - Excluir transacciones sin fecha
            transaction_date__date__gte=cutoff_date
        ).exists()
        
        if not recent_transactions:
            _create_alert_if_not_exists(
                rule=rule,
                product=product,
                title=f"📊 Sin movimiento: {product.name}",
                message=f"No hay movimientos en los últimos {days_threshold} días",
                severity='low',
                current_value=days_threshold,
                threshold_value=days_threshold
            )
            
    except Exception as e:
        logger.error(f"Error verificando sin movimiento: {str(e)}")

def _create_alert_if_not_exists(rule, product, title, message, severity, current_value, threshold_value):
    """Crea una alerta si no existe una similar reciente"""
    try:
        # Verificar si ya existe una alerta reciente (últimas 24 horas)
        recent_cutoff = timezone.now() - timedelta(hours=24)
        existing_alert = Alert.objects.filter(
            rule=rule,
            product=product,
            status__in=['active', 'acknowledged'],
            created_at__gte=recent_cutoff
        ).exists()
        
        if not existing_alert:
            # Crear nueva alerta
            alert = Alert.objects.create(
                company=rule.company,
                rule=rule,
                product=product,
                title=title,
                message=message,
                severity=severity,
                current_value=current_value,
                threshold_value=threshold_value,
                status='active'
            )
            
            logger.info(f"✅ Alerta automática creada: {title}")
            
            # Enviar notificaciones inmediatamente si está configurado
            if rule.frequency == 'immediate':
                try:
                    notification_service.send_alert_notification(alert)
                    logger.info(f"📧 Notificación enviada para alerta {alert.id}")
                except Exception as e:
                    logger.error(f"Error enviando notificación: {str(e)}")
            
            return alert
        else:
            logger.debug(f"🔄 Alerta ya existe para {product.name}")
            return None
            
    except Exception as e:
        logger.error(f"Error creando alerta automática: {str(e)}")
        return None