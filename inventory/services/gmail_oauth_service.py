"""
STUB: Gmail OAuth Service simplificado 
La funcionalidad se movió a TenantOnboardingService
"""
import logging

logger = logging.getLogger(__name__)


class GmailOAuthService:
    """Stub simplificado - funcionalidad movida a TenantOnboardingService"""
    
    def __init__(self):
        logger.info("GmailOAuthService: Funcionalidad movida a TenantOnboardingService")
    
    def get_authorization_url(self, *args, **kwargs):
        """Stub - usar TenantOnboardingService"""
        return "", ""
    
    def handle_oauth_callback(self, *args, **kwargs):
        """Stub - usar TenantOnboardingService"""
        return {
            'success': False,
            'error': 'OAuth manejado por TenantOnboardingService'
        }
    
    def setup_gmail_webhook(self, *args, **kwargs):
        """Stub - webhooks manejados por n8n"""
        return {
            'success': False,
            'error': 'Webhooks manejados por n8n'
        }
    
    def is_authenticated(self):
        """Stub"""
        return False
    
    def get_watch_status(self):
        """Stub"""
        return {
            'active': False,
            'message': 'Funcionalidad movida a n8n'
        }


# Instancia global stub
gmail_oauth_service = GmailOAuthService()
