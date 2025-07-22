"""
Servicio simplificado para integración con n8n
Solo maneja configuración y webhooks - La lógica está en n8n
"""
import logging
import requests
from django.conf import settings
from inventory.models import TenantConfig, PurchaseOrder

logger = logging.getLogger(__name__)


class N8nIntegrationService:
    """
    Servicio simple para integración con n8n
    """
    
    @staticmethod
    def get_tenant_config(company_id):
        """Obtener configuración del tenant"""
        try:
            config = TenantConfig.objects.get(company_id=company_id)
            return {
                'tenant_id': company_id,
                'oauth2_client_id': config.oauth2_client_id,
                'oauth2_client_secret': config.oauth2_client_secret,
                'oauth2_token_url': config.oauth2_token_url,
                'twilio_account_sid': config.twilio_account_sid,
                'twilio_auth_token': config.twilio_auth_token,
                'whatsapp_from_number': config.whatsapp_from_number,
                'gmail_client_id': config.gmail_client_id,
                'gmail_client_secret': config.gmail_client_secret,
                'gmail_access_token': config.gmail_access_token,
                'gmail_refresh_token': config.gmail_refresh_token,
                'gmail_email': config.gmail_email,
                'is_whatsapp_active': config.is_whatsapp_active,
                'is_gmail_active': config.is_gmail_active,
                'n8n_webhook_url': config.n8n_webhook_url,
                'is_configured': config.is_configured
            }
        except TenantConfig.DoesNotExist:
            return None
    
    @staticmethod
    def get_oauth_token(company_id):
        """
        Obtener token OAuth2 para el tenant usando Client Credentials Grant
        """
        try:
            config = N8nIntegrationService.get_tenant_config(company_id)
            if not config:
                return {'success': False, 'error': 'Configuración de tenant no encontrada'}
            
            # Preparar datos para Client Credentials Grant
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': config['oauth2_client_id'],
                'client_secret': config['oauth2_client_secret'],
                'scope': 'read write'
            }
            
            # Hacer request al token endpoint
            response = requests.post(
                config['oauth2_token_url'],
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                return {
                    'success': True,
                    'access_token': token_response.get('access_token'),
                    'token_type': token_response.get('token_type', 'Bearer'),
                    'expires_in': token_response.get('expires_in'),
                    'scope': token_response.get('scope')
                }
            else:
                logger.error(f"Error getting OAuth token: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Token request failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Exception getting OAuth token: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_order_to_n8n(purchase_order):
        """
        Enviar orden a n8n para procesamiento
        """
        try:
            tenant_config = N8nIntegrationService.get_tenant_config(
                purchase_order.company_id
            )
            
            if not tenant_config or not tenant_config['n8n_webhook_url']:
                logger.warning(f"No hay webhook n8n configurado para empresa {purchase_order.company_id}")
                return {'success': False, 'error': 'Webhook n8n no configurado'}
            
            # Preparar datos para n8n
            payload = {
                'order_id': purchase_order.id,
                'order_number': purchase_order.order_number,
                'tenant_id': purchase_order.company_id,
                'product': {
                    'name': purchase_order.product.name,
                    'sku': purchase_order.product.sku,
                    'quantity': purchase_order.quantity,
                    'unit_price': float(purchase_order.unit_price),
                    'total': float(purchase_order.total_amount)
                },
                'supplier': {
                    'name': purchase_order.supplier.name if purchase_order.supplier else None,
                    'email': purchase_order.supplier_email,
                    'whatsapp': purchase_order.supplier_whatsapp
                },
                'priority': purchase_order.priority,
                'notes': purchase_order.notes,
                'config': {
                    'whatsapp_enabled': tenant_config.is_whatsapp_active,
                    'gmail_enabled': tenant_config.is_gmail_active,
                    'whatsapp_from': tenant_config.whatsapp_from_number,
                    'gmail_from': tenant_config.gmail_email
                }
            }
            
            # Enviar a n8n
            response = requests.post(
                tenant_config['n8n_webhook_url'],
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Orden {purchase_order.order_number} enviada a n8n")
                return {'success': True, 'webhook_response': response.json()}
            else:
                logger.error(f"❌ Error webhook n8n: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"❌ Error conectando con n8n: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"❌ Error enviando a n8n: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_order_from_n8n(order_id, status, **kwargs):
        """
        Actualizar orden basada en callback de n8n
        """
        try:
            purchase_order = PurchaseOrder.objects.get(id=order_id)
            
            # Actualizar status
            purchase_order.status = status
            
            # Actualizar campos opcionales
            if kwargs.get('supplier_response'):
                purchase_order.supplier_response = kwargs['supplier_response']
            
            if kwargs.get('delivery_date'):
                purchase_order.expected_delivery_date = kwargs['delivery_date']
            
            if kwargs.get('notes'):
                purchase_order.notes = kwargs['notes']
            
            purchase_order.save()
            
            logger.info(f"✅ Orden {purchase_order.order_number} actualizada: {status}")
            return {'success': True, 'order': purchase_order}
            
        except PurchaseOrder.DoesNotExist:
            logger.error(f"❌ Orden {order_id} no encontrada")
            return {'success': False, 'error': 'Orden no encontrada'}
        except Exception as e:
            logger.error(f"❌ Error actualizando orden {order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
