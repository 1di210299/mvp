from django.apps import AppConfig


class AlertsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "alerts"
    
    def ready(self):
        """
        Se ejecuta cuando la app está lista
        Registra los signals para detección automática de alertas
        """
        import alerts.signals
