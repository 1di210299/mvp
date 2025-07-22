"""
STUB: EmailTrackingService simplificado para compatibilidad
La funcionalidad completa se movió a n8n workflows
"""
import logging

logger = logging.getLogger(__name__)


class EmailTrackingService:
    """Stub simplificado - funcionalidad movida a n8n"""
    
    def __init__(self, company_id=None):
        self.company_id = company_id
        logger.info("EmailTrackingService: Funcionalidad movida a n8n workflows")
    
    def send_tracked_email(self, *args, **kwargs):
        """Stub - usar n8n para email tracking"""
        return {
            'success': False,
            'error': 'Email tracking movido a n8n workflows. Usar APIs n8n.',
            'message': 'Use n8n integration for email tracking'
        }
    
    def process_gmail_webhook(self, *args, **kwargs):
        """Stub - webhooks manejados por n8n"""
        return {
            'success': False,
            'error': 'Gmail webhooks manejados por n8n'
        }
    
    def setup_gmail_api(self, *args, **kwargs):
        """Stub - OAuth manejado por TenantOnboardingService"""
        return False


def get_email_tracking_service(company_id=None):
    """Factory function stub"""
    return EmailTrackingService(company_id=company_id)


def send_tracked_email(*args, **kwargs):
    """Stub function - usar n8n para tracking"""
    return {
        'success': False,
        'error': 'Usar n8n APIs para email tracking'
    }


def analyze_email_patterns(*args, **kwargs):
    """Stub function - análisis movido a n8n"""
    return {
        'success': False,
        'patterns': [],
        'error': 'Email analysis movido a n8n workflows'
    }


def get_email_insights(*args, **kwargs):
    """Stub function - insights movidos a n8n"""
    return {
        'success': False,
        'insights': [],
        'error': 'Email insights movidos a n8n workflows'
    }
