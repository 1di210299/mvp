"""
Servicio para onboarding de tenants - configuración de Twilio y Gmail
"""
import logging
import json
from typing import Dict, Optional
from twilio.rest import Client as TwilioClient
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests

from django.conf import settings
from inventory.models.tenant_config import TenantConfig
from authentication.models import Company

logger = logging.getLogger(__name__)


class TenantOnboardingService:
    """
    Servicio para configurar automáticamente nuevos tenants con:
    - Subaccount de Twilio
    - Configuración de WhatsApp Business
    - OAuth2 de Gmail
    """
    
    def __init__(self):
        self.twilio_client = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
    
    def create_tenant_twilio_subaccount(self, company: Company) -> Dict:
        """
        Crear subaccount de Twilio para el tenant
        """
        try:
            # Crear subaccount
            subaccount = self.twilio_client.api.accounts.create(
                friendly_name=f"DataLens - {company.name}"
            )
            
            # Obtener Auth Token del subaccount
            subaccount_client = TwilioClient(
                subaccount.sid, 
                subaccount.auth_token
            )
            
            # Comprar número de teléfono (opcional)
            available_numbers = subaccount_client.available_phone_numbers('US').local.list(
                area_code='415',  # San Francisco area
                limit=1
            )
            
            phone_number = None
            if available_numbers:
                phone_number = subaccount_client.incoming_phone_numbers.create(
                    phone_number=available_numbers[0].phone_number
                )
            
            return {
                'success': True,
                'subaccount_sid': subaccount.sid,
                'auth_token': subaccount.auth_token,
                'phone_number': phone_number.phone_number if phone_number else None,
                'whatsapp_number': f"whatsapp:{phone_number.phone_number}" if phone_number else None
            }
            
        except Exception as e:
            logger.error(f"Error creando Twilio subaccount: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def setup_whatsapp_webhook(self, subaccount_sid: str, auth_token: str, webhook_url: str) -> Dict:
        """
        Configurar webhook de WhatsApp en Twilio
        """
        try:
            subaccount_client = TwilioClient(subaccount_sid, auth_token)
            
            # Configurar webhook para mensajes entrantes
            webhook = subaccount_client.applications.create(
                friendly_name="WhatsApp Webhook",
                message_url=webhook_url,
                message_method='POST'
            )
            
            return {
                'success': True,
                'webhook_sid': webhook.sid,
                'webhook_url': webhook_url
            }
            
        except Exception as e:
            logger.error(f"Error configurando WhatsApp webhook: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_gmail_oauth_url(self, company_id: int, redirect_uri: str) -> Dict:
        """
        Generar URL de autorización OAuth2 para Gmail
        """
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GMAIL_CLIENT_ID,
                        "client_secret": settings.GMAIL_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=[
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.modify'
                ]
            )
            
            flow.redirect_uri = redirect_uri
            
            # Generar URL de autorización
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=str(company_id)  # Para identificar el tenant
            )
            
            return {
                'success': True,
                'auth_url': auth_url,
                'state': state
            }
            
        except Exception as e:
            logger.error(f"Error generando Gmail OAuth URL: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_gmail_oauth_callback(self, code: str, state: str, redirect_uri: str) -> Dict:
        """
        Procesar callback de OAuth2 y guardar tokens
        """
        try:
            company_id = int(state)
            company = Company.objects.get(id=company_id)
            
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GMAIL_CLIENT_ID,
                        "client_secret": settings.GMAIL_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=[
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.modify'
                ]
            )
            
            flow.redirect_uri = redirect_uri
            
            # Intercambiar código por tokens
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            # Guardar tokens en TenantConfig
            tenant_config, created = TenantConfig.objects.get_or_create(
                company=company
            )
            
            tenant_config.gmail_access_token = credentials.token
            tenant_config.gmail_refresh_token = credentials.refresh_token
            tenant_config.gmail_token_expiry = credentials.expiry
            tenant_config.gmail_enabled = True
            tenant_config.save()
            
            return {
                'success': True,
                'message': 'Gmail OAuth configurado exitosamente',
                'company_id': company_id
            }
            
        except Exception as e:
            logger.error(f"Error procesando Gmail OAuth callback: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def complete_tenant_setup(self, company: Company, admin_email: str) -> Dict:
        """
        Configuración completa de un tenant nuevo
        """
        try:
            results = {
                'company_id': company.id,
                'company_name': company.name,
                'steps': {}
            }
            
            # 1. Crear configuración base
            tenant_config, created = TenantConfig.objects.get_or_create(
                company=company
            )
            results['steps']['tenant_config'] = {
                'success': True,
                'created': created
            }
            
            # 2. Configurar Twilio subaccount
            twilio_result = self.create_tenant_twilio_subaccount(company)
            results['steps']['twilio_setup'] = twilio_result
            
            if twilio_result['success']:
                # Guardar configuración de Twilio
                tenant_config.twilio_account_sid = twilio_result['subaccount_sid']
                tenant_config.twilio_auth_token = twilio_result['auth_token']
                tenant_config.twilio_whatsapp_number = twilio_result.get('whatsapp_number')
                tenant_config.twilio_enabled = True
                tenant_config.save()
            
            # 3. Generar URL de Gmail OAuth
            redirect_uri = f"{settings.FRONTEND_URL}/oauth/gmail/callback"
            gmail_oauth_result = self.generate_gmail_oauth_url(company.id, redirect_uri)
            results['steps']['gmail_oauth'] = gmail_oauth_result
            
            # 4. Configurar webhooks (si tenemos URLs)
            if hasattr(settings, 'N8N_WEBHOOK_BASE_URL'):
                webhook_url = f"{settings.N8N_WEBHOOK_BASE_URL}/whatsapp/{company.id}"
                webhook_result = self.setup_whatsapp_webhook(
                    twilio_result.get('subaccount_sid'),
                    twilio_result.get('auth_token'),
                    webhook_url
                )
                results['steps']['webhook_setup'] = webhook_result
            
            return {
                'success': True,
                'results': results,
                'next_steps': [
                    "El administrador debe completar la autorización de Gmail",
                    "Configurar número de WhatsApp Business en Meta",
                    "Probar envío de mensajes desde n8n"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error en setup completo del tenant: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_tenant_configuration(self, company: Company) -> Dict:
        """
        Validar que la configuración del tenant esté completa
        """
        try:
            tenant_config = TenantConfig.objects.get(company=company)
            
            validation_results = {
                'twilio_configured': tenant_config.twilio_enabled and bool(tenant_config.twilio_account_sid),
                'gmail_configured': tenant_config.gmail_enabled and bool(tenant_config.gmail_access_token),
                'whatsapp_number': bool(tenant_config.twilio_whatsapp_number),
                'is_fully_configured': False
            }
            
            validation_results['is_fully_configured'] = all([
                validation_results['twilio_configured'],
                validation_results['gmail_configured'],
                validation_results['whatsapp_number']
            ])
            
            return {
                'success': True,
                'validation': validation_results,
                'configuration': tenant_config
            }
            
        except TenantConfig.DoesNotExist:
            return {
                'success': False,
                'error': 'Configuración de tenant no encontrada'
            }
        except Exception as e:
            logger.error(f"Error validando configuración: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
