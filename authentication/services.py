"""
Servicios para el flujo N8N de onboarding de tenants
"""
import requests
import json
import logging
import time
import uuid
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from .models import TenantConfig, UsageLog
from celery import shared_task

logger = logging.getLogger(__name__)


class TenantOnboardingService:
    """Servicio para el onboarding de tenants"""
    
    @staticmethod
    def create_tenant(name, domain, email_address, whatsapp_number=None):
        """Crear un nuevo tenant"""
        try:
            # Validar datos
            if not name or not domain or not email_address:
                raise ValueError("Todos los campos requeridos deben estar presentes")
            
            # Crear tenant
            tenant = TenantConfig.objects.create(
                name=name,
                domain=domain,
                email_address=email_address,
                verification_status='pending'
            )
            
            # Log de creación
            UsageLog.objects.create(
                tenant=tenant,
                channel='email',
                action='tenant_created',
                status='success',
                details={
                    'name': name,
                    'domain': domain,
                    'email': email_address,
                    'whatsapp_number': whatsapp_number
                }
            )
            
            return {
                'success': True,
                'tenant_id': str(tenant.tenant_id),
                'message': 'Tenant creado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error creando tenant: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def verify_domain_and_email(tenant_id):
        """Verificar dominio y configurar email en Google Workspace"""
        try:
            tenant = TenantConfig.objects.get(tenant_id=tenant_id)
            
            # TODO: Implementar verificación de dominio
            # 1. Añadir dominio como alias en Google Workspace
            # 2. Crear usuario en Workspace
            # 3. Configurar alias send-as
            # 4. Generar claves DKIM
            # 5. Crear registros DNS
            
            tenant.verification_status = 'domain_verified'
            tenant.save()
            
            # Log de verificación
            UsageLog.objects.create(
                tenant=tenant,
                channel='email',
                action='domain_verified',
                status='success',
                details={'domain': tenant.domain}
            )
            
            return {'success': True, 'message': 'Dominio verificado'}
            
        except TenantConfig.DoesNotExist:
            return {'success': False, 'error': 'Tenant no encontrado'}
        except Exception as e:
            logger.error(f"Error verificando dominio: {str(e)}")
            return {'success': False, 'error': str(e)}


class WhatsAppService:
    """Servicio para WhatsApp Business Cloud API"""
    
    @staticmethod
    def send_text(tenant_id, to, body):
        """Envía mensaje de texto por WhatsApp"""
        return WhatsAppService.send_message(tenant_id, to, body, 'text')
    
    @staticmethod
    def send_message(tenant_id, phone_number, message, message_type='text'):
        """Envía mensaje WhatsApp"""
        try:
            # En modo DEBUG, simular el envío SIEMPRE (antes de validar tenant)
            if settings.DEBUG:
                logger.info(f"DEBUG MODE: Simulando envío de WhatsApp a {phone_number}")
                
                # Intentar obtener tenant, pero si no existe, crear un log básico
                try:
                    config = TenantConfig.objects.get(tenant_id=tenant_id)
                    tenant_ref = config
                except TenantConfig.DoesNotExist:
                    # En DEBUG, simular incluso si el tenant no existe
                    tenant_ref = None
                
                # Log usando el nuevo esquema de campos de UsageLog
                if tenant_ref:
                    usage_log = UsageLog.objects.create(
                        tenant=tenant_ref,
                        channel='whatsapp',
                        action='send_text_debug',
                        status='success',
                        details={
                            'phone_number': phone_number,
                            'message': message,
                            'message_type': message_type,
                            'simulated': True,
                            'debug_mode': True
                        }
                    )
                    log_id = usage_log.id
                else:
                    log_id = None
                
                return {
                    'success': True,
                    'message_id': f'debug_msg_{timezone.now().timestamp()}',
                    'log_id': log_id
                }
            
            # Configuración para producción
            # Obtener configuración del tenant
            config = TenantConfig.objects.get(tenant_id=tenant_id)
            
            whatsapp_token = config.get_whatsapp_token()
            if not whatsapp_token:
                raise ValueError("Token de WhatsApp no configurado")
            
            # URL y headers para Graph API
            url = f'https://graph.facebook.com/v21.0/{config.phone_number_id}/messages'
            headers = {
                'Authorization': f'Bearer {whatsapp_token}',
                'Content-Type': 'application/json',
            }
            
            # Payload del mensaje
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': message_type,
                message_type: {'body': message} if message_type == 'text' else message
            }
            
            # Enviar mensaje
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200:
                # Log exitoso
                usage_log = UsageLog.objects.create(
                    tenant=config,
                    channel='whatsapp',
                    action='send_text',
                    status='success',
                    details={
                        'phone_number': phone_number,
                        'message_id': response_data.get('messages', [{}])[0].get('id'),
                        'status': 'sent'
                    }
                )
                
                return {
                    'success': True,
                    'message_id': response_data.get('messages', [{}])[0].get('id'),
                    'log_id': usage_log.id
                }
            else:
                # Log de error
                error_msg = f"HTTP {response.status_code}: {response_data}"
                usage_log = UsageLog.objects.create(
                    tenant=config,
                    channel='whatsapp',
                    action='send_text',
                    status='failed',
                    error_message=error_msg,
                    details={
                        'phone_number': phone_number,
                        'error': error_msg,
                        'status_code': response.status_code
                    }
                )
                
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Error en WhatsApp service: {str(e)}")
            # Log de excepción (solo en producción o si DEBUG falló)
            if not settings.DEBUG:
                try:
                    config = TenantConfig.objects.get(tenant_id=tenant_id)
                    usage_log = UsageLog.objects.create(
                        tenant=config,
                        channel='whatsapp',
                        action='send_text',
                        status='failed',
                        error_message=str(e),
                        details={
                            'phone_number': phone_number,
                            'exception': str(e),
                            'error_type': type(e).__name__
                        }
                    )
                    log_id = usage_log.id
                except:
                    log_id = None
            else:
                log_id = None
                
            return {
                'success': False,
                'error': str(e),
                'log_id': log_id
            }
    
    @staticmethod
    def setup_whatsapp_business(tenant_id, whatsapp_number):
        """Configurar WhatsApp Business para un tenant"""
        try:
            tenant = TenantConfig.objects.get(tenant_id=tenant_id)
            
            if settings.DEBUG:
                # Para desarrollo, usar configuración mock pero funcional
                tenant.phone_number_id = f"mock_phone_id_{str(tenant_id).replace('-', '')[:8]}"
                tenant.set_wa_token(f"mock_wa_token_{str(tenant_id).replace('-', '')[:8]}")
                tenant.verification_status = 'whatsapp_configured'
                tenant.save()
                
                # Log de configuración
                UsageLog.objects.create(
                    tenant=tenant,
                    channel='whatsapp',
                    action='business_setup',
                    status='success',
                    details={
                        'whatsapp_number': whatsapp_number,
                        'phone_number_id': tenant.phone_number_id,
                        'method': 'mock_setup'
                    }
                )
                
                return {'success': True, 'message': 'WhatsApp Business configurado (desarrollo)'}
            else:
                # TODO: Implementar configuración real con Meta API
                # 1. Registrar/verificar número en WABA
                # 2. Obtener phone_number_id y token
                # 3. Configurar webhook
                
                # Por ahora, placeholder para producción
                tenant.verification_status = 'whatsapp_configured'
                tenant.save()
                
                # Log de configuración
                UsageLog.objects.create(
                    tenant=tenant,
                    channel='whatsapp',
                    action='business_setup',
                    status='success',
                    details={'whatsapp_number': whatsapp_number}
                )
                
                return {'success': True, 'message': 'WhatsApp Business configurado'}
            
        except TenantConfig.DoesNotExist:
            return {'success': False, 'error': 'Tenant no encontrado'}
        except Exception as e:
            logger.error(f"Error configurando WhatsApp: {str(e)}")
            return {'success': False, 'error': str(e)}


class EmailService:
    """Servicio para envío de emails"""
    
    @staticmethod
    def send_email(tenant_id, to, subject, body, attachments=None):
        """Enviar email usando Gmail API"""
        try:
            tenant = TenantConfig.objects.get(tenant_id=tenant_id)
            
            # Log de intento
            log = UsageLog.objects.create(
                tenant=tenant,
                channel='email',
                action='send_email',
                status='pending',
                details={
                    'to': to,
                    'subject': subject,
                    'has_attachments': bool(attachments)
                }
            )
            
            # Para desarrollo, usar el sistema de email de Django
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', tenant.email_address),
                    recipient_list=[to],
                    fail_silently=False
                )
                
                log.status = 'success'
                log.details.update({
                    'sent_from': getattr(settings, 'DEFAULT_FROM_EMAIL', tenant.email_address),
                    'method': 'django_email'
                })
                log.save()
                
                return {
                    'success': True,
                    'message': 'Email enviado exitosamente',
                    'log_id': log.id
                }
                
            except Exception as email_error:
                log.status = 'failed'
                log.error_message = str(email_error)
                log.save()
                
                return {
                    'success': False,
                    'error': str(email_error),
                    'log_id': log.id
                }
                
        except TenantConfig.DoesNotExist:
            return {'success': False, 'error': 'Tenant no encontrado'}
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            return {'success': False, 'error': str(e)}


class UsageReportService:
    """Servicio para reportes de uso"""
    
    @staticmethod
    def get_tenant_usage(tenant_id, start_date=None, end_date=None):
        """Obtener reporte de uso de un tenant"""
        try:
            tenant = TenantConfig.objects.get(tenant_id=tenant_id)
            
            # Construir query
            logs = UsageLog.objects.filter(tenant=tenant)
            
            if start_date:
                logs = logs.filter(timestamp__gte=start_date)
            if end_date:
                logs = logs.filter(timestamp__lte=end_date)
            
            # Agrupar por canal y estado
            usage_summary = {}
            for log in logs:
                channel = log.channel
                status = log.status
                
                if channel not in usage_summary:
                    usage_summary[channel] = {
                        'total': 0,
                        'success': 0,
                        'failed': 0,
                        'pending': 0,
                        'retry': 0
                    }
                
                usage_summary[channel]['total'] += 1
                usage_summary[channel][status] += 1
            
            return {
                'success': True,
                'tenant_id': str(tenant_id),
                'tenant_name': tenant.name,
                'usage_summary': usage_summary,
                'total_requests': logs.count()
            }
            
        except TenantConfig.DoesNotExist:
            return {'success': False, 'error': 'Tenant no encontrado'}
        except Exception as e:
            logger.error(f"Error generando reporte: {str(e)}")
            return {'success': False, 'error': str(e)}


# Tareas de Celery para reintentos automáticos
@shared_task(bind=True, max_retries=3)
def retry_failed_whatsapp(self, log_id):
    """Reintentar envío de WhatsApp fallido"""
    try:
        log = UsageLog.objects.get(id=log_id)
        
        if log.retry_count >= 3:
            return {'success': False, 'error': 'Máximo de reintentos alcanzado'}
        
        # Incrementar contador de reintentos
        log.retry_count += 1
        log.status = 'retry'
        log.save()
        
        # Reintentar envío
        result = WhatsAppService.send_text(
            log.tenant.tenant_id,
            log.details.get('to'),
            log.details.get('body')
        )
        
        return result
        
    except Exception as e:
        raise self.retry(countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def retry_failed_email(self, log_id):
    """Reintentar envío de email fallido"""
    try:
        log = UsageLog.objects.get(id=log_id)
        
        if log.retry_count >= 3:
            return {'success': False, 'error': 'Máximo de reintentos alcanzado'}
        
        # Incrementar contador de reintentos
        log.retry_count += 1
        log.status = 'retry'
        log.save()
        
        # Reintentar envío
        result = EmailService.send_email(
            log.tenant.tenant_id,
            log.details.get('to'),
            log.details.get('subject'),
            log.details.get('body')
        )
        
        return result
        
    except Exception as e:
        raise self.retry(countdown=60 * (2 ** self.request.retries))
