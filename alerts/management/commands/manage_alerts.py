from django.core.management.base import BaseCommand
from django.utils import timezone
from alerts.models import AlertRule, Alert
from alerts.tasks import check_all_alerts, check_alert_rule
from authentication.models import Company


class Command(BaseCommand):
    help = 'Gestiona el sistema de alertas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-all',
            action='store_true',
            help='Verificar todas las reglas de alerta activas',
        )
        parser.add_argument(
            '--check-rule',
            type=int,
            help='Verificar una regla específica por ID',
        )
        parser.add_argument(
            '--list-rules',
            action='store_true',
            help='Listar todas las reglas de alerta',
        )
        parser.add_argument(
            '--list-alerts',
            action='store_true',
            help='Listar alertas recientes',
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de la empresa (opcional)',
        )
        parser.add_argument(
            '--create-sample-rule',
            action='store_true',
            help='Crear una regla de ejemplo',
        )

    def handle(self, *args, **options):
        if options['check_all']:
            self.check_all_alerts()
        elif options['check_rule']:
            self.check_single_rule(options['check_rule'])
        elif options['list_rules']:
            self.list_alert_rules(options.get('company_id'))
        elif options['list_alerts']:
            self.list_recent_alerts(options.get('company_id'))
        elif options['create_sample_rule']:
            self.create_sample_rule(options.get('company_id'))
        else:
            self.stdout.write(self.style.ERROR('Debe especificar una acción'))

    def check_all_alerts(self):
        self.stdout.write('Iniciando verificación de todas las reglas de alerta...')
        task = check_all_alerts.delay()
        self.stdout.write(
            self.style.SUCCESS(f'Tarea iniciada con ID: {task.id}')
        )

    def check_single_rule(self, rule_id):
        try:
            rule = AlertRule.objects.get(id=rule_id)
            self.stdout.write(f'Verificando regla: {rule.name}')
            task = check_alert_rule.delay(rule_id)
            self.stdout.write(
                self.style.SUCCESS(f'Tarea iniciada con ID: {task.id}')
            )
        except AlertRule.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Regla con ID {rule_id} no encontrada')
            )

    def list_alert_rules(self, company_id=None):
        queryset = AlertRule.objects.all()
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        self.stdout.write('\n=== Reglas de Alerta ===')
        for rule in queryset:
            status = '✅' if rule.is_active else '❌'
            self.stdout.write(
                f'{status} [{rule.id}] {rule.name} - {rule.get_alert_type_display()}'
            )
            self.stdout.write(f'   Empresa: {rule.company.name}')
            self.stdout.write(f'   Frecuencia: {rule.get_frequency_display()}')
            if rule.threshold_value:
                self.stdout.write(f'   Umbral: {rule.threshold_value}')
            if rule.threshold_percentage:
                self.stdout.write(f'   Porcentaje: {rule.threshold_percentage}%')
            self.stdout.write('')

    def list_recent_alerts(self, company_id=None):
        queryset = Alert.objects.all()
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        recent_alerts = queryset.order_by('-created_at')[:20]
        
        self.stdout.write('\n=== Alertas Recientes ===')
        for alert in recent_alerts:
            status_icon = {
                'active': '🔴',
                'acknowledged': '🟡',
                'resolved': '✅',
                'dismissed': '❌'
            }.get(alert.status, '❓')
            
            severity_icon = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'critical': '🔴'
            }.get(alert.severity, '❓')
            
            self.stdout.write(
                f'{status_icon} {severity_icon} [{alert.id}] {alert.title}'
            )
            self.stdout.write(f'   Estado: {alert.get_status_display()}')
            self.stdout.write(f'   Severidad: {alert.get_severity_display()}')
            self.stdout.write(f'   Fecha: {alert.created_at}')
            if alert.product:
                self.stdout.write(f'   Producto: {alert.product.name}')
            if alert.location:
                self.stdout.write(f'   Ubicación: {alert.location.name}')
            self.stdout.write('')

    def create_sample_rule(self, company_id=None):
        try:
            if company_id:
                company = Company.objects.get(id=company_id)
            else:
                company = Company.objects.first()
                if not company:
                    self.stdout.write(
                        self.style.ERROR('No hay empresas disponibles')
                    )
                    return
            
            # Crear regla de stock bajo
            rule = AlertRule.objects.create(
                company=company,
                name='Stock Bajo - Ejemplo',
                description='Regla de ejemplo para alertas de stock bajo',
                alert_type='low_stock',
                threshold_value=10,
                send_email=True,
                send_notification=True,
                frequency='immediate',
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Regla de ejemplo creada: {rule.name} (ID: {rule.id})'
                )
            )
            
        except Company.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Empresa con ID {company_id} no encontrada')
            )
