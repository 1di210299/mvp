"""
Tareas de Celery para órdenes de compra automáticas
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q, Count, Sum
from datetime import timedelta
import logging

from inventory.services.purchase_order_service import PurchaseOrderService
from inventory.models import PurchaseOrder
from authentication.models import Company

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def check_low_stock_and_generate_orders(self, company_id=None):
    """
    Tarea programada para verificar stock bajo y generar órdenes automáticamente
    Se ejecuta diariamente a las 08:00
    """
    try:
        purchase_service = PurchaseOrderService()
        
        if company_id:
            # Procesar empresa específica
            try:
                company = Company.objects.get(id=company_id)
                results = purchase_service.check_low_stock_and_generate_orders(company=company)
                
                logger.info(f"Proceso completado para {company.name}: {results}")
                return results
                
            except Company.DoesNotExist:
                error_msg = f"Empresa con ID {company_id} no encontrada"
                logger.error(error_msg)
                return {'error': error_msg}
        
        else:
            # Procesar todas las empresas activas
            companies = Company.objects.filter(is_active=True)
            all_results = {
                'companies_processed': 0,
                'total_orders_generated': 0,
                'total_emails_sent': 0,
                'company_results': []
            }
            
            for company in companies:
                try:
                    logger.info(f"Procesando empresa: {company.name}")
                    results = purchase_service.check_low_stock_and_generate_orders(company=company)
                    
                    if 'error' not in results:
                        all_results['companies_processed'] += 1
                        all_results['total_orders_generated'] += results.get('orders_generated', 0)
                        all_results['total_emails_sent'] += results.get('emails_sent', 0)
                        
                        all_results['company_results'].append({
                            'company_id': company.id,
                            'company_name': company.name,
                            'results': results
                        })
                    
                except Exception as e:
                    logger.error(f"Error procesando empresa {company.name}: {str(e)}")
                    all_results['company_results'].append({
                        'company_id': company.id,
                        'company_name': company.name,
                        'error': str(e)
                    })
            
            logger.info(f"Proceso global completado: {all_results}")
            return all_results
    
    except Exception as e:
        logger.error(f"Error en tarea de órdenes automáticas: {str(e)}")
        return {'error': str(e)}


@shared_task(bind=True)
def send_pending_purchase_order_emails(self):
    """
    Enviar emails pendientes de órdenes de compra
    Se ejecuta cada 2 horas
    """
    try:
        purchase_service = PurchaseOrderService()
        
        # Buscar órdenes que pueden ser enviadas
        pending_orders = PurchaseOrder.objects.filter(
            status='draft',
            email_sent=False,
            supplier_email__isnull=False
        ).exclude(supplier_email='')
        
        results = {
            'orders_processed': 0,
            'emails_sent': 0,
            'errors': []
        }
        
        for order in pending_orders:
            try:
                results['orders_processed'] += 1
                
                # Enviar email
                success = purchase_service._send_purchase_order_email(order)
                
                if success:
                    results['emails_sent'] += 1
                    logger.info(f"Email enviado para orden {order.order_number}")
                else:
                    results['errors'].append(f"Error enviando email para orden {order.order_number}")
                
            except Exception as e:
                error_msg = f"Error procesando orden {order.order_number}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        logger.info(f"Emails pendientes procesados: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error enviando emails pendientes: {str(e)}")
        return {'error': str(e)}


@shared_task(bind=True)
def check_overdue_orders(self):
    """
    Verificar órdenes vencidas y enviar alertas
    Se ejecuta diariamente a las 10:00
    """
    try:
        today = timezone.now().date()
        
        # Buscar órdenes vencidas
        overdue_orders = PurchaseOrder.objects.filter(
            expected_delivery_date__lt=today,
            status__in=['sent', 'confirmed', 'in_transit']
        ).select_related('product', 'supplier', 'company')
        
        results = {
            'overdue_orders_found': overdue_orders.count(),
            'alerts_created': 0,
            'companies_notified': set()
        }
        
        for order in overdue_orders:
            try:
                # Crear alerta de orden vencida
                from alerts.models import Alert
                
                days_overdue = (today - order.expected_delivery_date).days
                
                Alert.objects.get_or_create(
                    company=order.company,
                    product=order.product,
                    title=f"Orden de Compra Vencida: {order.order_number}",
                    defaults={
                        'message': f"La orden {order.order_number} para {order.product.name} "
                                 f"está vencida por {days_overdue} días. "
                                 f"Fecha esperada: {order.expected_delivery_date}",
                        'severity': 'high' if days_overdue > 7 else 'medium',
                        'status': 'active',
                        'source': 'system',
                        'current_value': days_overdue,
                        'threshold_value': 0,
                        'context_data': {
                            'purchase_order_id': order.id,
                            'order_number': order.order_number,
                            'days_overdue': days_overdue
                        }
                    }
                )
                
                results['alerts_created'] += 1
                results['companies_notified'].add(order.company.name)
                
            except Exception as e:
                logger.error(f"Error creando alerta para orden {order.order_number}: {str(e)}")
        
        results['companies_notified'] = list(results['companies_notified'])
        logger.info(f"Verificación de órdenes vencidas completada: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error verificando órdenes vencidas: {str(e)}")
        return {'error': str(e)}


@shared_task(bind=True)
def send_weekly_purchase_order_summary(self):
    """
    Enviar resumen semanal de órdenes de compra
    Se ejecuta los lunes a las 09:00
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from django.db.models import Count, Sum
        
        # Calcular fecha de la semana pasada
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        results = {
            'companies_processed': 0,
            'emails_sent': 0,
            'errors': []
        }
        
        # Procesar por empresa
        companies = Company.objects.filter(is_active=True)
        
        for company in companies:
            try:
                # Estadísticas de la semana
                weekly_orders = PurchaseOrder.objects.filter(
                    company=company,
                    created_at__date__gte=week_ago
                )
                
                if not weekly_orders.exists():
                    continue  # No enviar si no hay órdenes
                
                stats = weekly_orders.aggregate(
                    total_orders=Count('id'),
                    total_amount=Sum('total_amount'),
                    sent_orders=Count('id', filter=Q(status='sent')),
                    received_orders=Count('id', filter=Q(status='received'))
                )
                
                # Preparar email
                subject = f"[DataLens] Resumen Semanal de Órdenes de Compra - {company.name}"
                
                message = f"""
Resumen de Órdenes de Compra - Semana del {week_ago} al {today}

ESTADÍSTICAS GENERALES:
• Total de órdenes generadas: {stats['total_orders']}
• Monto total: S/ {stats['total_amount'] or 0:.2f}
• Órdenes enviadas: {stats['sent_orders']}
• Órdenes recibidas: {stats['received_orders']}

ÓRDENES PENDIENTES:
"""
                
                # Añadir órdenes pendientes
                pending_orders = weekly_orders.filter(status__in=['draft', 'sent'])
                for order in pending_orders[:10]:  # Máximo 10
                    message += f"• {order.order_number} - {order.product.name} - S/ {order.total_amount}\n"
                
                if pending_orders.count() > 10:
                    message += f"... y {pending_orders.count() - 10} órdenes más\n"
                
                message += f"""

Para revisar todas las órdenes, ingrese al sistema DataLens.

Saludos,
Sistema Automático DataLens
                """
                
                # Obtener email de la empresa o admin
                company_email = getattr(company, 'email', None)
                if not company_email:
                    # Buscar admin de la empresa
                    admin_users = company.users.filter(is_staff=True, email_notifications=True)
                    if admin_users.exists():
                        company_email = admin_users.first().email
                
                if company_email:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[company_email],
                        fail_silently=False
                    )
                    
                    results['emails_sent'] += 1
                    logger.info(f"Resumen semanal enviado a {company.name}")
                
                results['companies_processed'] += 1
                
            except Exception as e:
                error_msg = f"Error enviando resumen a {company.name}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        logger.info(f"Resumen semanal completado: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error enviando resumen semanal: {str(e)}")
        return {'error': str(e)}


@shared_task(bind=True)
def cleanup_old_purchase_order_logs(self):
    """
    Limpiar logs antiguos de emails (más de 90 días)
    Se ejecuta mensualmente
    """
    try:
        from inventory.models import PurchaseOrderEmailLog
        
        cutoff_date = timezone.now() - timedelta(days=90)
        
        deleted_count, _ = PurchaseOrderEmailLog.objects.filter(
            sent_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Limpieza de logs completada: {deleted_count} registros eliminados")
        return {'deleted_logs': deleted_count}
        
    except Exception as e:
        logger.error(f"Error limpiando logs: {str(e)}")
        return {'error': str(e)}
