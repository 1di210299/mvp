"""
Comando para crear reglas de alerta básicas automáticamente
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from alerts.models import AlertRule
from authentication.models import Company
from inventory.models import Category


class Command(BaseCommand):
    help = 'Crea reglas de alerta básicas para el sistema automático'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de la empresa para crear las reglas',
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Empresa con ID {company_id} no encontrada')
                )
                return
        else:
            # Usar la primera empresa disponible
            company = Company.objects.first()
            if not company:
                self.stdout.write(
                    self.style.ERROR('No hay empresas en el sistema')
                )
                return

        self.stdout.write(f'🏢 Creando reglas para empresa: {company.name}')
        
        # Crear reglas básicas
        rules_created = 0
        
        # 1. Regla de stock bajo general
        rule1, created = AlertRule.objects.get_or_create(
            company=company,
            name='Stock Bajo General',
            alert_type='low_stock',
            defaults={
                'description': 'Alerta cuando cualquier producto tiene stock bajo',
                'threshold_value': 10,
                'frequency': 'immediate',
                'is_active': True,
                'send_email': True,
                'send_whatsapp': False,
                'send_notification': True,
            }
        )
        if created:
            rules_created += 1
            self.stdout.write(f'✅ Regla creada: {rule1.name}')

        # 2. Regla de stock crítico
        rule2, created = AlertRule.objects.get_or_create(
            company=company,
            name='Stock Crítico',
            alert_type='low_stock',
            defaults={
                'description': 'Alerta crítica cuando el stock es muy bajo',
                'threshold_value': 5,
                'frequency': 'immediate',
                'is_active': True,
                'send_email': True,
                'send_whatsapp': True,
                'send_notification': True,
            }
        )
        if created:
            rules_created += 1
            self.stdout.write(f'✅ Regla creada: {rule2.name}')

        # 3. Regla de stock negativo
        rule3, created = AlertRule.objects.get_or_create(
            company=company,
            name='Stock Negativo',
            alert_type='negative_stock',
            defaults={
                'description': 'Alerta cuando el stock es negativo',
                'threshold_value': 0,
                'frequency': 'immediate',
                'is_active': True,
                'send_email': True,
                'send_whatsapp': True,
                'send_notification': True,
            }
        )
        if created:
            rules_created += 1
            self.stdout.write(f'✅ Regla creada: {rule3.name}')

        # 4. Regla de productos próximos a vencer
        rule4, created = AlertRule.objects.get_or_create(
            company=company,
            name='Próximo Vencimiento',
            alert_type='expiration',
            defaults={
                'description': 'Alerta cuando productos están próximos a vencer',
                'days_before_expiration': 7,
                'frequency': 'daily',
                'is_active': True,
                'send_email': True,
                'send_whatsapp': False,
                'send_notification': True,
            }
        )
        if created:
            rules_created += 1
            self.stdout.write(f'✅ Regla creada: {rule4.name}')

        # 5. Regla de productos vencidos
        rule5, created = AlertRule.objects.get_or_create(
            company=company,
            name='Productos Vencidos',
            alert_type='expired',
            defaults={
                'description': 'Alerta cuando productos han vencido',
                'frequency': 'immediate',
                'is_active': True,
                'send_email': True,
                'send_whatsapp': True,
                'send_notification': True,
            }
        )
        if created:
            rules_created += 1
            self.stdout.write(f'✅ Regla creada: {rule5.name}')

        # 6. Regla de alta demanda
        rule6, created = AlertRule.objects.get_or_create(
            company=company,
            name='Alta Demanda',
            alert_type='high_demand',
            defaults={
                'description': 'Alerta cuando hay alta demanda de un producto',
                'threshold_value': 50,
                'frequency': 'immediate',
                'is_active': True,
                'send_email': True,
                'send_whatsapp': False,
                'send_notification': True,
            }
        )
        if created:
            rules_created += 1
            self.stdout.write(f'✅ Regla creada: {rule6.name}')

        # 7. Regla de stock alto
        rule7, created = AlertRule.objects.get_or_create(
            company=company,
            name='Stock Alto',
            alert_type='high_stock',
            defaults={
                'description': 'Alerta cuando hay exceso de stock',
                'threshold_value': 1000,
                'frequency': 'weekly',
                'is_active': True,
                'send_email': True,
                'send_whatsapp': False,
                'send_notification': True,
            }
        )
        if created:
            rules_created += 1
            self.stdout.write(f'✅ Regla creada: {rule7.name}')

        # 8. Regla de productos sin movimiento
        rule8, created = AlertRule.objects.get_or_create(
            company=company,
            name='Sin Movimiento',
            alert_type='no_movement',
            defaults={
                'description': 'Alerta cuando productos no tienen movimiento',
                'threshold_value': 30,  # días
                'frequency': 'weekly',
                'is_active': True,
                'send_email': True,
                'send_whatsapp': False,
                'send_notification': True,
            }
        )
        if created:
            rules_created += 1
            self.stdout.write(f'✅ Regla creada: {rule8.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Proceso completado! Se crearon {rules_created} nuevas reglas de alerta.\n'
                f'📋 Total de reglas activas: {AlertRule.objects.filter(company=company, is_active=True).count()}\n'
                f'🚨 El sistema ahora detectará automáticamente cambios en:\n'
                f'   • Stock de productos (bajo, alto, negativo)\n'
                f'   • Fechas de vencimiento\n'
                f'   • Transacciones y demanda\n'
                f'   • Niveles de inventario\n'
                f'   • Productos sin movimiento\n\n'
                f'💡 Para probar el sistema:\n'
                f'   1. Ve al dashboard de alertas: http://localhost:8081/app/alerts\n'
                f'   2. Haz clic en "Verificar Alertas"\n'
                f'   3. Cambia el stock de algún producto en inventario\n'
                f'   4. Las alertas se generarán automáticamente!\n'
            )
        )