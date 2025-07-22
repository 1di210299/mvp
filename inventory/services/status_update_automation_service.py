"""
STUB: Status Update Automation Service simplificado
La funcionalidad se movió a n8n workflows
"""
import logging

logger = logging.getLogger(__name__)


class StatusUpdateAutomationService:
    """Stub simplificado - funcionalidad movida a n8n"""
    
    def __init__(self):
        logger.info("StatusUpdateAutomationService: Funcionalidad movida a n8n workflows")
    
    def process_email_for_status_updates(self, *args, **kwargs):
        """Stub - procesamiento movido a n8n"""
        return []
    
    def setup_automation_rules(self, *args, **kwargs):
        """Stub - reglas manejadas en n8n"""
        return {
            'success': False,
            'error': 'Automation rules configuradas en n8n workflows'
        }


def get_status_update_service():
    """Factory function stub"""
    return StatusUpdateAutomationService()
