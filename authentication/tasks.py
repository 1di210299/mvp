"""
Tareas de Celery para el flujo N8N
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging
import time
import requests
from datetime import timedelta

from .models import TenantConfig, UsageLog
from .services import WhatsAppService, EmailService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def retry_failed_whatsapp_message(self, log_id):
    """
    Reintentar envío de mensaje de WhatsApp fallido
    """
    try:
        log = UsageLog.objects.get(id=log_id, channel='whatsapp', status='failed')
        
        # Verificar si ya se alcanzó el máximo de reintentos
        if log.retry_count >= getattr(settings, 'MAX_RETRY_ATTEMPTS', 3):
            logger.warning(f"Máximo de reintentos alcanzado para log {log_id}")
            return {
                'success': False,
                'error': 'Máximo de reintentos alcanzado'
            }
        
        # Incrementar contador de reintentos
        log.retry_count += 1
        log.status = 'retry'
        log.save()
        
        logger.info(f"Reintentando envío de WhatsApp (intento {log.retry_count}): {log_id}")
        
        # Reintentar el envío
        result = WhatsAppService.send_text(
            tenant_id=log.tenant.tenant_id,
            to=log.details.get('to'),
            body=log.details.get('body')
        )
        
        if result['success']:
            # Actualizar el log original como exitoso
            log.status = 'success'
            log.error_message = None
            log.details.update({
                'retry_successful': True,
                'final_attempt': log.retry_count
            })
            log.save()
            
            logger.info(f"Reintento exitoso para log {log_id}")
            return result
        else:
            # Si falla, programar otro reintento si no se alcanzó el máximo
            if log.retry_count < getattr(settings, 'MAX_RETRY_ATTEMPTS', 3):
                delay = getattr(settings, 'RETRY_DELAY_SECONDS', 60) * (2 ** log.retry_count)
                self.retry(countdown=delay)
            else:
                log.status = 'failed'
                log.error_message = f"Falló después de {log.retry_count} reintentos: {result['error']}"
                log.save()
            
            return result
            
    except UsageLog.DoesNotExist:
        logger.error(f"Log {log_id} no encontrado")
        return {'success': False, 'error': 'Log no encontrado'}
    except Exception as e:
        logger.error(f"Error en retry_failed_whatsapp_message: {str(e)}")
        raise self.retry(countdown=60)


@shared_task(bind=True, max_retries=3)
def retry_failed_email(self, log_id):
    """
    Reintentar envío de email fallido
    """
    try:
        log = UsageLog.objects.get(id=log_id, channel='email', status='failed')
        
        if log.retry_count >= getattr(settings, 'MAX_RETRY_ATTEMPTS', 3):
            logger.warning(f"Máximo de reintentos alcanzado para email log {log_id}")
            return {
                'success': False,
                'error': 'Máximo de reintentos alcanzado'
            }
        
        log.retry_count += 1
        log.status = 'retry'
        log.save()
        
        logger.info(f"Reintentando envío de email (intento {log.retry_count}): {log_id}")
        
        result = EmailService.send_email(
            tenant_id=log.tenant.tenant_id,
            to=log.details.get('to'),
            subject=log.details.get('subject'),
            body=log.details.get('body'),
            attachments=log.details.get('attachments')
        )
        
        if result['success']:
            log.status = 'success'
            log.error_message = None
            log.details.update({
                'retry_successful': True,
                'final_attempt': log.retry_count
            })
            log.save()
            
            logger.info(f"Reintento de email exitoso para log {log_id}")
            return result
        else:
            if log.retry_count < getattr(settings, 'MAX_RETRY_ATTEMPTS', 3):
                delay = getattr(settings, 'RETRY_DELAY_SECONDS', 60) * (2 ** log.retry_count)
                self.retry(countdown=delay)
            else:
                log.status = 'failed'
                log.error_message = f"Falló después de {log.retry_count} reintentos: {result['error']}"
                log.save()
            
            return result
            
    except UsageLog.DoesNotExist:
        logger.error(f"Email log {log_id} no encontrado")
        return {'success': False, 'error': 'Log no encontrado'}
    except Exception as e:
        logger.error(f"Error en retry_failed_email: {str(e)}")
        raise self.retry(countdown=60)


@shared_task
def process_pending_domain_verifications():
    """
    Procesar verificaciones de dominio pendientes (cron job)
    """
    try:
        # Buscar tenants con verificación pendiente
        pending_tenants = TenantConfig.objects.filter(
            verification_status__in=['pending', 'domain_verified'],
            is_active=False
        )
        
        results = []
        for tenant in pending_tenants:
            try:
                # TODO: Implementar verificación real de propagación DNS
                # Por ahora, mock de verificación
                if tenant.verification_status == 'pending':
                    # Simular verificación de dominio
                    tenant.verification_status = 'domain_verified'
                    tenant.save()
                    
                    # Log del proceso
                    UsageLog.objects.create(
                        tenant=tenant,
                        channel='email',
                        action='domain_verification_check',
                        status='success',
                        details={'status': 'domain_verified'}
                    )
                    
                    results.append({
                        'tenant_id': str(tenant.tenant_id),
                        'status': 'domain_verified'
                    })
                    
                elif tenant.verification_status == 'domain_verified':
                    # Verificar si WhatsApp está configurado
                    if tenant.phone_number_id and tenant.get_wa_token():
                        tenant.verification_status = 'completed'
                        tenant.is_active = True
                        tenant.save()
                        
                        UsageLog.objects.create(
                            tenant=tenant,
                            channel='email',
                            action='tenant_activation',
                            status='success',
                            details={'status': 'completed', 'activated': True}
                        )
                        
                        results.append({
                            'tenant_id': str(tenant.tenant_id),
                            'status': 'completed'
                        })
                        
            except Exception as e:
                logger.error(f"Error procesando tenant {tenant.tenant_id}: {str(e)}")
                
                UsageLog.objects.create(
                    tenant=tenant,
                    channel='email',
                    action='domain_verification_check',
                    status='failed',
                    error_message=str(e)
                )
        
        logger.info(f"Procesadas {len(results)} verificaciones de dominio")
        return {
            'success': True,
            'processed': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error en process_pending_domain_verifications: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_usage_logs():
    """
    Limpiar logs de uso antiguos (cron job)
    """
    try:
        # Eliminar logs más antiguos que 30 días
        cutoff_date = timezone.now() - timedelta(days=30)
        
        old_logs = UsageLog.objects.filter(timestamp__lt=cutoff_date)
        count = old_logs.count()
        old_logs.delete()
        
        logger.info(f"Eliminados {count} logs antiguos")
        return {
            'success': True,
            'deleted_count': count
        }
        
    except Exception as e:
        logger.error(f"Error en cleanup_old_usage_logs: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def send_usage_report_email():
    """
    Enviar reporte de uso por email (cron job semanal)
    """
    try:
        # Obtener estadísticas de la última semana
        start_date = timezone.now() - timedelta(days=7)
        
        stats = {}
        for tenant in TenantConfig.objects.filter(is_active=True):
            logs = UsageLog.objects.filter(
                tenant=tenant,
                timestamp__gte=start_date
            )
            
            stats[str(tenant.tenant_id)] = {
                'name': tenant.name,
                'domain': tenant.domain,
                'total_requests': logs.count(),
                'successful_requests': logs.filter(status='success').count(),
                'failed_requests': logs.filter(status='failed').count(),
                'channels': {}
            }
            
            # Estadísticas por canal
            for channel in ['whatsapp', 'email', 'ocr', 'ia']:
                channel_logs = logs.filter(channel=channel)
                stats[str(tenant.tenant_id)]['channels'][channel] = {
                    'total': channel_logs.count(),
                    'success': channel_logs.filter(status='success').count(),
                    'failed': channel_logs.filter(status='failed').count()
                }
        
        # TODO: Enviar email con estadísticas a administradores
        logger.info("Reporte de uso generado exitosamente")
        
        return {
            'success': True,
            'stats': stats,
            'period': '7 days'
        }
        
    except Exception as e:
        logger.error(f"Error en send_usage_report_email: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def health_check_tenants():
    """
    Verificar el estado de salud de los tenants (cron job)
    """
    try:
        results = []
        
        for tenant in TenantConfig.objects.filter(is_active=True):
            try:
                # Verificar conectividad con WhatsApp
                whatsapp_status = 'ok'
                if tenant.phone_number_id and tenant.get_wa_token():
                    # TODO: Hacer ping a la API de WhatsApp
                    pass
                else:
                    whatsapp_status = 'not_configured'
                
                # Verificar configuración de email
                email_status = 'ok'
                gsuite_key = tenant.get_gsuite_key()
                if not gsuite_key:
                    email_status = 'not_configured'
                
                # Log del health check
                UsageLog.objects.create(
                    tenant=tenant,
                    channel='email',
                    action='health_check',
                    status='success',
                    details={
                        'whatsapp_status': whatsapp_status,
                        'email_status': email_status
                    }
                )
                
                results.append({
                    'tenant_id': str(tenant.tenant_id),
                    'name': tenant.name,
                    'whatsapp_status': whatsapp_status,
                    'email_status': email_status,
                    'overall_status': 'healthy' if whatsapp_status == 'ok' and email_status == 'ok' else 'issues'
                })
                
            except Exception as e:
                logger.error(f"Error en health check para tenant {tenant.tenant_id}: {str(e)}")
                
                UsageLog.objects.create(
                    tenant=tenant,
                    channel='email',
                    action='health_check',
                    status='failed',
                    error_message=str(e)
                )
                
                results.append({
                    'tenant_id': str(tenant.tenant_id),
                    'name': tenant.name,
                    'overall_status': 'error',
                    'error': str(e)
                })
        
        logger.info(f"Health check completado para {len(results)} tenants")
        return {
            'success': True,
            'checked_tenants': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error en health_check_tenants: {str(e)}")
        return {'success': False, 'error': str(e)}
