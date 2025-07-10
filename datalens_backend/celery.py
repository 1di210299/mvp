# Configuración Celery para DataLens
import os
from celery import Celery
from django.conf import settings

# Configurar Django settings module para celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')

app = Celery('datalens_backend')

# Usar configuración de Django para Celery con configuración explícita
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuración adicional para asegurar compatibilidad
app.conf.update(
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    result_backend_transport_options={
        'retry_policy': {
            'timeout': 5.0
        }
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=True,
)

# Autodescubrir tareas en todas las aplicaciones Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Configurar tareas programadas
app.conf.beat_schedule = {
    'check-alerts-every-hour': {
        'task': 'alerts.tasks.check_all_alerts',
        'schedule': 60.0 * 60.0,  # Cada hora
    },
    'train-forecast-models-weekly': {
        'task': 'forecasting.tasks.train_all_models',
        'schedule': 60.0 * 60.0 * 24.0 * 7.0,  # Cada semana
    },
    'generate-reports-daily': {
        'task': 'reports.tasks.generate_scheduled_reports',
        'schedule': 60.0 * 60.0 * 24.0,  # Cada día
    },
}

app.conf.timezone = 'America/Lima'
