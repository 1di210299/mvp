"""
Gmail OAuth2 Service
Maneja la autenticación OAuth2 con Gmail API y configuración de webhooks
"""
import json
import logging
import secrets
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.urls import reverse

# Google Auth imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

from inventory.services.pubsub_service import pubsub_service

logger = logging.getLogger(__name__)

# Scopes necesarios para Gmail API con webhooks
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.metadata'
]


class GmailOAuthService:
    """
    Servicio para manejar OAuth2 con Gmail API
    """
    
    def __init__(self):
        self.client_id = settings.GMAIL_CLIENT_ID
        self.client_secret = settings.GMAIL_CLIENT_SECRET
        self.redirect_uri = settings.GMAIL_REDIRECT_URI
        
        self.credentials = None
        self.service = None
        
        if GMAIL_API_AVAILABLE and self.client_id and self.client_secret:
            self._load_credentials()
    
    def is_available(self) -> bool:
        """Verificar si Gmail OAuth está disponible"""
        return (
            GMAIL_API_AVAILABLE and 
            self.client_id and 
            self.client_secret and
            self.redirect_uri
        )
    
    def _load_credentials(self):
        """Cargar credenciales guardadas"""
        try:
            # Intentar cargar desde cache
            creds_data = cache.get('gmail_oauth_credentials')
            if creds_data:
                self.credentials = Credentials.from_authorized_user_info(creds_data, GMAIL_SCOPES)
                
                # Verificar si las credenciales son válidas
                if self.credentials and self.credentials.valid:
                    self._initialize_service()
                    logger.info("✅ Credenciales Gmail cargadas desde cache")
                elif self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Intentar refrescar credenciales
                    self.credentials.refresh(Request())
                    self._save_credentials()
                    self._initialize_service()
                    logger.info("✅ Credenciales Gmail refrescadas")
                
        except Exception as e:
            logger.warning(f"⚠️  No se pudieron cargar credenciales Gmail: {e}")
            self.credentials = None
    
    def _save_credentials(self):
        """Guardar credenciales en cache"""
        try:
            if self.credentials:
                creds_data = {
                    'token': self.credentials.token,
                    'refresh_token': self.credentials.refresh_token,
                    'token_uri': self.credentials.token_uri,
                    'client_id': self.credentials.client_id,
                    'client_secret': self.credentials.client_secret,
                    'scopes': self.credentials.scopes
                }
                # Guardar por 1 hora (las credenciales se refrescan automáticamente)
                cache.set('gmail_oauth_credentials', creds_data, timeout=3600)
                logger.info("💾 Credenciales Gmail guardadas en cache")
                
        except Exception as e:
            logger.error(f"❌ Error guardando credenciales: {e}")
    
    def _initialize_service(self):
        """Inicializar servicio de Gmail"""
        try:
            if self.credentials:
                self.service = build('gmail', 'v1', credentials=self.credentials)
                logger.info("🔧 Servicio Gmail inicializado")
                
        except Exception as e:
            logger.error(f"❌ Error inicializando servicio Gmail: {e}")
            self.service = None
    
    def get_authorization_url(self, user_id: str = None) -> Tuple[str, str]:
        """
        Generar URL de autorización OAuth2
        Returns: (authorization_url, state)
        """
        try:
            # Configurar flow OAuth2
            client_config = {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            }
            
            flow = Flow.from_client_config(
                client_config,
                scopes=GMAIL_SCOPES,
                redirect_uri=self.redirect_uri
            )
            
            # Generar state para seguridad
            state = secrets.token_urlsafe(32)
            
            # Guardar user_id en el state para recuperar después
            state_data = {
                'state': state,
                'user_id': user_id,
                'timestamp': cache.time()
            }
            cache.set(f'gmail_oauth_state_{state}', state_data, timeout=600)  # 10 minutos
            
            # Generar URL de autorización
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state,
                prompt='consent'  # Forzar consent para obtener refresh_token
            )
            
            logger.info(f"🔗 URL de autorización generada para user {user_id}")
            return authorization_url, state
            
        except Exception as e:
            logger.error(f"❌ Error generando URL de autorización: {e}")
            return "", ""
    
    def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Manejar callback de OAuth2
        """
        try:
            # Verificar state
            state_data = cache.get(f'gmail_oauth_state_{state}')
            if not state_data:
                return {'success': False, 'error': 'State inválido o expirado'}
            
            # Limpiar state del cache
            cache.delete(f'gmail_oauth_state_{state}')
            
            # Configurar flow OAuth2
            client_config = {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            }
            
            flow = Flow.from_client_config(
                client_config,
                scopes=GMAIL_SCOPES,
                redirect_uri=self.redirect_uri
            )
            
            # Intercambiar código por credenciales
            flow.fetch_token(code=code)
            self.credentials = flow.credentials
            
            # Guardar credenciales
            self._save_credentials()
            
            # Inicializar servicio
            self._initialize_service()
            
            # Configurar webhook automáticamente
            webhook_result = self.setup_gmail_webhook()
            
            user_id = state_data.get('user_id')
            
            logger.info(f"✅ OAuth callback exitoso para user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'webhook_configured': webhook_result.get('success', False),
                'message': 'Autorización exitosa'
            }
            
        except Exception as e:
            logger.error(f"❌ Error en OAuth callback: {e}")
            return {'success': False, 'error': str(e)}
    
    def setup_gmail_webhook(self) -> Dict[str, Any]:
        """
        Configurar webhook de Gmail para recibir notificaciones
        """
        try:
            if not self.service:
                return {'success': False, 'error': 'Servicio Gmail no inicializado'}
            
            # 1. Setup Pub/Sub
            if not pubsub_service.setup_gmail_webhook():
                return {'success': False, 'error': 'Error configurando Pub/Sub'}
            
            # 2. Configurar watch en Gmail
            topic_name = pubsub_service.get_topic_path()
            
            watch_request = {
                'topicName': topic_name,
                'labelIds': ['INBOX'],  # Monitorear solo INBOX por ahora
                'labelFilterAction': 'include'
            }
            
            # Llamar a Gmail API para configurar watch
            result = self.service.users().watch(userId='me', body=watch_request).execute()
            
            # Guardar información del watch
            watch_data = {
                'historyId': result.get('historyId'),
                'expiration': result.get('expiration'),
                'topic_name': topic_name
            }
            cache.set('gmail_watch_data', watch_data, timeout=7*24*3600)  # 7 días
            
            logger.info(f"✅ Gmail webhook configurado: {result}")
            
            return {
                'success': True,
                'history_id': result.get('historyId'),
                'expiration': result.get('expiration'),
                'topic_name': topic_name
            }
            
        except Exception as e:
            logger.error(f"❌ Error configurando Gmail webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def stop_gmail_webhook(self) -> Dict[str, Any]:
        """
        Detener webhook de Gmail
        """
        try:
            if not self.service:
                return {'success': False, 'error': 'Servicio Gmail no inicializado'}
            
            # Llamar a Gmail API para detener watch
            result = self.service.users().stop(userId='me').execute()
            
            # Limpiar datos del watch
            cache.delete('gmail_watch_data')
            
            logger.info("✅ Gmail webhook detenido")
            
            return {'success': True, 'message': 'Webhook detenido'}
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo Gmail webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_watch_status(self) -> Dict[str, Any]:
        """
        Obtener estado del watch de Gmail
        """
        try:
            watch_data = cache.get('gmail_watch_data')
            if not watch_data:
                return {'active': False, 'message': 'No hay watch activo'}
            
            return {
                'active': True,
                'history_id': watch_data.get('historyId'),
                'expiration': watch_data.get('expiration'),
                'topic_name': watch_data.get('topic_name')
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado del watch: {e}")
            return {'active': False, 'error': str(e)}
    
    def is_authenticated(self) -> bool:
        """Verificar si está autenticado"""
        return self.credentials is not None and self.credentials.valid


# Instancia global del servicio
gmail_oauth_service = GmailOAuthService()
