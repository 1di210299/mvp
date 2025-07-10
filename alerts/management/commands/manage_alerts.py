from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from alerts.models import Alert, AlertRule
from inventory.models import Product, InventoryItem
from authentication.models import Company
from datalens_backend.utils import get_default_company


class Command(BaseCommand):
    help = 'Gestiona alertas automáticas del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-stock',
            action='store_true',
            help='Verificar niveles de stock y generar alertas',
        )
        parser.add_argument(
            '--check-expiration',
            action='store_true',
            help='Verificar productos próximos a vencer',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Limpiar alertas antiguas resueltas',
        )

    def handle(self, *args, **options):
        if options['check_stock']:
            self.check_stock_levels()
        
        if options['check_expiration']:
            self.check_product_expiration()
            
        if options['cleanup']:
            self.cleanup_old_alerts()

    def check_stock_levels(self):
        """Verifica niveles de stock y genera alertas"""
        company = get_default_company()
        if not company:
            self.stdout.write('No se encontró empresa para verificar stock')
            return

        low_stock_items = InventoryItem.objects.filter(
            company=company,
            quantity__lte=F('product__minimum_stock'),
            product__is_active=True
        ).select_related('product')

        for item in low_stock_items:
            alert, created = Alert.objects.get_or_create(
                company=company,
                product=item.product,
                alert_type='low_stock',
                defaults={
                    'title': 'Stock Bajo',
                    'description': f'El producto {item.product.name} tiene un stock bajo.',
                    'severity': 'medium',
                    'status': 'active',
                    'created_at': timezone.now(),
                    'updated_at': timezone.now(),
                }
            )

            if created:
                self.stdout.write(f'¡Alerta creada! {alert.description}')
            else:
                self.stdout.write(f'La alerta ya existe: {alert.description}')

    def check_product_expiration(self):
        """Verifica productos próximos a vencer y genera alertas"""
        company = get_default_company()
        if not company:
            self.stdout.write('No se encontró empresa para verificar expiración de productos')
            return

        soon_to_expire_products = Product.objects.filter(
            company=company,
            expiration_date__lte=timezone.now() + timedelta(days=7),
            is_active=True
        )

        for product in soon_to_expire_products:
            alert, created = Alert.objects.get_or_create(
                company=company,
                product=product,
                alert_type='expiration',
                defaults={
                    'title': 'Producto Próximo a Vencer',
                    'description': f'El producto {product.name} está próximo a vencer.',
                    'severity': 'high',
                    'status': 'active',
                    'created_at': timezone.now(),
                    'updated_at': timezone.now(),
                }
            )

            if created:
                self.stdout.write(f'¡Alerta de expiración creada! {alert.description}')
            else:
                self.stdout.write(f'La alerta de expiración ya existe: {alert.description}')

    def cleanup_old_alerts(self):
        """Elimina alertas antiguas que han sido resueltas"""
        threshold_date = timezone.now() - timedelta(days=30)
        old_alerts = Alert.objects.filter(
            updated_at__lt=threshold_date,
            status='resolved'
        )

        deleted_count, _ = old_alerts.delete()
        self.stdout.write(f'Se eliminaron {deleted_count} alertas antiguas')
