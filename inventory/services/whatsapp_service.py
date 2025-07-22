"""
Servicio de WhatsApp para envío de órdenes de compra y mensajes automatizados
Soporta Twilio WhatsApp API y Meta WhatsApp Business Cloud API
"""
import logging
import json
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Servicio principal para WhatsApp - Multi-empresa"""
    
    def __init__(self, company=None):
        self.company = company
        self.twilio_service = TwilioWhatsAppService(company=company)
        self.meta_service = MetaWhatsAppService(company=company)
        self.default_service = 'twilio'  # Default fallback
    
    def send_purchase_order_message(self, purchase_order, recipient_number=None):
        """Enviar mensaje de orden de compra por WhatsApp usando configuración de la empresa"""
        try:
            # Usar la empresa de la orden de compra
            if not self.company and purchase_order.company:
                self.company = purchase_order.company
                self.twilio_service = TwilioWhatsAppService(company=self.company)
                self.meta_service = MetaWhatsAppService(company=self.company)
            
            # Verificar que la empresa tenga WhatsApp habilitado
            if not self.company or not self.company.whatsapp_enabled:
                logger.warning(f"WhatsApp no habilitado para empresa {self.company.name if self.company else 'N/A'}")
                return {'success': False, 'error': 'WhatsApp no habilitado para esta empresa'}
            
            # Determinar destinatario
            if not recipient_number:
                recipient_number = purchase_order.supplier_whatsapp
                if not recipient_number and purchase_order.supplier:
                    recipient_number = purchase_order.supplier.whatsapp_number
            
            if not recipient_number:
                logger.warning(f"No hay número WhatsApp para orden {purchase_order.order_number}")
                return {'success': False, 'error': 'No hay número WhatsApp configurado'}
            
            # Generar mensaje personalizado por empresa
            message = self.generate_purchase_order_message(purchase_order)
            
            # Intentar enviar con Meta API primero (si está configurado para esta empresa)
            if self._is_meta_configured():
                result = self.meta_service.send_message(recipient_number, message)
                if result['success']:
                    self._log_whatsapp_sent(purchase_order, recipient_number, 'meta', result.get('message_id'))
                    return result
            
            # Fallback a Twilio (si está configurado para esta empresa)
            if self._is_twilio_configured():
                result = self.twilio_service.send_message(recipient_number, message)
                if result['success']:
                    self._log_whatsapp_sent(purchase_order, recipient_number, 'twilio', result.get('message_id'))
                    return result
            
            return {'success': False, 'error': 'No hay servicios WhatsApp configurados'}
            
        except Exception as e:
            logger.error(f"Error enviando WhatsApp para orden {purchase_order.order_number}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_purchase_order_message(self, purchase_order):
        """Generar mensaje WhatsApp para orden de compra usando templates"""
        try:
            from .whatsapp_templates import WhatsAppTemplates
            return WhatsAppTemplates.purchase_order_template(purchase_order)
        except ImportError:
            # Fallback al método anterior si no está disponible
            return self._generate_basic_message(purchase_order)
    
    def _generate_basic_message(self, purchase_order):
        """Generar mensaje básico de orden de compra (fallback)"""
        priority_emoji = {
            'low': '🔵',
            'medium': '🟡', 
            'high': '🟠',
            'urgent': '🔴'
        }
        
        emoji = priority_emoji.get(purchase_order.priority, '📋')
        
        message = f"""{emoji} *ORDEN DE COMPRA*

*Orden:* {purchase_order.order_number}
*Empresa:* {purchase_order.company.name}

📦 *PRODUCTO:*
• {purchase_order.product.name}
• SKU: {purchase_order.product.sku}
• Cantidad: {purchase_order.quantity} unidades
• Precio unitario: S/ {purchase_order.unit_price}
• *Total: S/ {purchase_order.total_amount}*

⏰ *DETALLES:*
• Prioridad: {purchase_order.get_priority_display()}
• Fecha esperada: {purchase_order.expected_delivery_date}

✅ *Por favor confirme:*
1. Disponibilidad del producto
2. Tiempo de entrega
3. Condiciones de pago

📞 *Contacto:*
{getattr(purchase_order.company, 'phone', 'No especificado')}

_Mensaje automático - Sistema DataLens_"""
        
        return message
    
    def send_webhook_response(self, phone_number, message_text):
        """SIMPLIFICADO: Webhook response ahora manejado por n8n"""
        try:
            logger.info(f"📱 Mensaje WhatsApp recibido: {phone_number} - Procesamiento movido a n8n")
            
            # Respuesta básica para mantener compatibilidad
            basic_response = """📱 *Mensaje recibido*

Tu mensaje ha sido registrado. Nuestro sistema automatizado procesará tu respuesta.

_Sistema DataLens - Procesamiento automático_"""
            
            # Enviar respuesta básica
            if self._is_meta_configured():
                return self.meta_service.send_message(phone_number, basic_response)
            elif self._is_twilio_configured():
                return self.twilio_service.send_message(phone_number, basic_response)
            
            return {'success': False, 'error': 'No hay servicios WhatsApp configurados'}
            
        except Exception as e:
            logger.error(f"Error procesando webhook WhatsApp: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ===========================================
    # MÉTODOS SIMPLIFICADOS (lógica compleja movida a n8n)
    # ===========================================
    
    def _is_twilio_configured(self):
        """Verificar si Twilio está configurado para esta empresa"""
        # Prioridad 1: Configuración específica de la empresa
        if self.company:
            return (
                self.company.twilio_account_sid and
                self.company.twilio_auth_token and
                self.company.twilio_whatsapp_from
            )
        
        # Prioridad 2: Configuración global en settings
        return (
            hasattr(settings, 'TWILIO_ACCOUNT_SID') and
            hasattr(settings, 'TWILIO_AUTH_TOKEN') and
            settings.TWILIO_ACCOUNT_SID and
            settings.TWILIO_AUTH_TOKEN
        )
    
    def _is_meta_configured(self):
        """Verificar si Meta WhatsApp está configurado para esta empresa"""
        # Prioridad 1: Configuración específica de la empresa
        if self.company:
            return (
                self.company.meta_whatsapp_access_token and
                self.company.meta_whatsapp_phone_number_id
            )
        
        # Prioridad 2: Configuración global en settings
        return (
            hasattr(settings, 'META_WHATSAPP_TOKEN') and
            hasattr(settings, 'META_WHATSAPP_PHONE_ID') and
            settings.META_WHATSAPP_TOKEN and
            settings.META_WHATSAPP_PHONE_ID
        )
    
    def _log_whatsapp_sent(self, purchase_order, recipient, service, message_id):
        """Registrar envío de WhatsApp"""
        try:
            purchase_order.whatsapp_sent = True
            purchase_order.whatsapp_sent_at = timezone.now()
            purchase_order.whatsapp_message_id = message_id
            purchase_order.supplier_whatsapp = recipient
            
            # Actualizar método de envío
            if purchase_order.email_sent and purchase_order.whatsapp_sent:
                purchase_order.sent_method = 'both'
            elif purchase_order.whatsapp_sent:
                purchase_order.sent_method = 'whatsapp'
            
            purchase_order.save()
            
            logger.info(f"✅ WhatsApp enviado: {purchase_order.order_number} -> {recipient} via {service}")
            
        except Exception as e:
            logger.error(f"Error registrando envío WhatsApp: {str(e)}")


class TwilioWhatsAppService:
    """Servicio específico para Twilio WhatsApp API"""
    
    def __init__(self, company=None):
        self.company = company
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
    
    def send_message(self, to_number, message_text):
        """Enviar mensaje via Twilio WhatsApp"""
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            # Formatear números
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            message = client.messages.create(
                body=message_text,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"📱 Twilio WhatsApp enviado: {message.sid}")
            
            return {
                'success': True,
                'message_id': message.sid,
                'service': 'twilio'
            }
            
        except Exception as e:
            logger.error(f"Error Twilio WhatsApp: {str(e)}")
            return {'success': False, 'error': str(e)}


class MetaWhatsAppService:
    """Servicio para Meta WhatsApp Business Cloud API (GRATIS)"""
    
    def __init__(self, company=None):
        self.company = company
        self.access_token = getattr(settings, 'META_WHATSAPP_TOKEN', '')
        self.phone_number_id = getattr(settings, 'META_WHATSAPP_PHONE_ID', '')
        self.api_version = 'v21.0'
        self.base_url = f'https://graph.facebook.com/{self.api_version}'
    
    def send_message(self, to_number, message_text):
        """Enviar mensaje via Meta WhatsApp Business API"""
        try:
            import requests
            
            # Limpiar número (quitar whatsapp: prefix si existe)
            if to_number.startswith('whatsapp:'):
                to_number = to_number.replace('whatsapp:', '')
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': to_number,
                'type': 'text',
                'text': {
                    'body': message_text
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', '')
            
            logger.info(f"📱 Meta WhatsApp enviado: {message_id}")
            
            return {
                'success': True,
                'message_id': message_id,
                'service': 'meta',
                'response': result
            }
            
        except Exception as e:
            logger.error(f"Error Meta WhatsApp: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def send_template_message(self, to_number, template_name, parameters=None):
        """Enviar mensaje con template pre-aprobado"""
        try:
            import requests
            
            if to_number.startswith('whatsapp:'):
                to_number = to_number.replace('whatsapp:', '')
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': to_number,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {
                        'code': 'es'  # Español
                    }
                }
            }
            
            # Agregar parámetros si existen
            if parameters:
                payload['template']['components'] = [{
                    'type': 'body',
                    'parameters': parameters
                }]
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', '')
            
            logger.info(f"📱 Meta WhatsApp template enviado: {template_name} -> {message_id}")
            
            return {
                'success': True,
                'message_id': message_id,
                'service': 'meta',
                'template': template_name,
                'response': result
            }
            
        except Exception as e:
            logger.error(f"Error Meta WhatsApp template: {str(e)}")
            return {'success': False, 'error': str(e)}


# ✅ Instancia global del servicio
whatsapp_service = WhatsAppService()
