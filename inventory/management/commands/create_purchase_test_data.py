"""
Comando para crear datos de prueba específicos para el sistema de órdenes de compra
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.models import Product, Supplier
from authentication.models import Company
from alerts.models import AlertRule
import random


class Command(BaseCommand):
    help = 'Crear datos de prueba para el sistema de órdenes de compra'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de empresa específica para crear datos'
        )
        parser.add_argument(
            '--products-count',
            type=int,
            default=5,
            help='Número de productos a crear'
        )
        parser.add_argument(
            '--low-stock-ratio',
            type=float,
            default=0.8,
            help='Proporción de productos con stock bajo (0.0-1.0)'
        )
    
    def handle(self, *args, **options):
        """Crear datos de prueba para órdenes de compra"""
        
        self.stdout.write('🔧 Creando datos de prueba para órdenes de compra...')
        
        # Obtener empresa
        company_id = options.get('company_id')
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                self.stdout.write(f'📋 Usando empresa: {company.name}')
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Empresa {company_id} no encontrada')
                )
                return
        else:
            # Usar la primera empresa activa
            company = Company.objects.filter(is_active=True).first()
            if not company:
                self.stdout.write(
                    self.style.ERROR('❌ No hay empresas activas')
                )
                return
            self.stdout.write(f'📋 Usando empresa: {company.name} (ID: {company.id})')
        
        # Configuración
        products_count = options.get('products_count', 5)
        low_stock_ratio = options.get('low_stock_ratio', 0.8)
        low_stock_count = int(products_count * low_stock_ratio)
        
        # Crear proveedor de prueba
        supplier = self._create_test_supplier(company)
        
        # Crear regla de alerta
        alert_rule = self._create_alert_rule(company)
        
        # Crear productos
        products_created = []
        
        for i in range(products_count):
            is_low_stock = i < low_stock_count
            
            product = self._create_test_product(
                company=company,
                supplier=supplier,
                index=i + 1,
                low_stock=is_low_stock
            )
            
            products_created.append(product)
            
            status_icon = "🔴" if is_low_stock else "🟢"
            self.stdout.write(
                f'   {status_icon} {product.name}: Stock {product.stock}/{product.min_stock}'
            )
        
        # Mostrar resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📊 DATOS CREADOS')
        self.stdout.write('='*60)
        self.stdout.write(f'🏢 Empresa: {company.name} (ID: {company.id})')
        self.stdout.write(f'🏭 Proveedor: {supplier.name} ({supplier.email})')
        self.stdout.write(f'📦 Productos totales: {products_count}')
        self.stdout.write(f'🔴 Productos con stock bajo: {low_stock_count}')
        self.stdout.write(f'🟢 Productos con stock normal: {products_count - low_stock_count}')
        self.stdout.write(f'🚨 Regla de alerta: {alert_rule.name}')
        self.stdout.write('='*60)
        
        # Comando para probar
        self.stdout.write('\n💡 Para probar el sistema ejecuta:')
        self.stdout.write(
            self.style.WARNING(
                f'python manage.py generate_purchase_orders --dry-run --company-id {company.id}'
            )
        )
    
    def _create_test_supplier(self, company):
        """Crear proveedor de prueba"""
        
        supplier_name = f"Proveedor Prueba {company.name[:20]}"
        
        supplier, created = Supplier.objects.get_or_create(
            name=supplier_name,
            defaults={
                'email': f'proveedor.prueba@{company.name.lower().replace(" ", "")}.com',
                'phone': '+51-999-888-777',
                'address': 'Av. Industrial 123, Lima, Perú',
                'contact_name': 'Juan Pérez',
                'payment_terms': '30 días',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✅ Proveedor creado: {supplier.name}')
        else:
            self.stdout.write(f'ℹ️ Proveedor existente: {supplier.name}')
        
        return supplier
    
    def _create_alert_rule(self, company):
        """Crear regla de alerta para órdenes automáticas"""
        
        rule_name = f"Orden Automática - {company.name[:20]}"
        
        rule, created = AlertRule.objects.get_or_create(
            name=rule_name,
            company=company,
            defaults={
                'alert_type': 'low_stock',
                'threshold_value': 15,
                'is_active': True,
                'auto_generate_purchase_orders': True,
                'auto_send_purchase_emails': True,
                'purchase_order_priority': 'medium'
            }
        )
        
        if created:
            self.stdout.write(f'✅ Regla de alerta creada: {rule.name}')
        else:
            rule.auto_generate_purchase_orders = True
            rule.auto_send_purchase_emails = True
            rule.save()
            self.stdout.write(f'ℹ️ Regla de alerta actualizada: {rule.name}')
        
        return rule
    
    def _create_test_product(self, company, supplier, index, low_stock=True):
        """Crear producto de prueba"""
        
        categories = ['Electrónicos', 'Hogar', 'Oficina', 'Ferretería', 'Limpieza']
        category = random.choice(categories)
        
        product_name = f"Producto Prueba {category} {index:02d}"
        sku = f"TEST-{category[:3].upper()}-{index:03d}"
        
        # Configurar stock según parámetro
        if low_stock:
            min_stock = random.randint(20, 50)
            max_stock = min_stock * 3
            current_stock = random.randint(1, min_stock - 5)  # Stock bajo
        else:
            min_stock = random.randint(10, 30)
            max_stock = min_stock * 3
            current_stock = random.randint(min_stock + 5, max_stock)  # Stock normal
        
        product, created = Product.objects.get_or_create(
            sku=sku,
            company=company,
            defaults={
                'name': product_name,
                'description': f'Producto de prueba para el sistema de órdenes automáticas',
                'stock': current_stock,
                'min_stock': min_stock,
                'max_stock': max_stock,
                'cost_price': round(random.uniform(10.0, 100.0), 2),
                'sale_price': round(random.uniform(15.0, 150.0), 2),
                'supplier': supplier,
                'unit': random.choice(['und', 'kg', 'lt', 'mt']),
                'is_active': True
            }
        )
        
        if not created:
            # Actualizar producto existente
            product.stock = current_stock
            product.min_stock = min_stock
            product.max_stock = max_stock
            product.supplier = supplier
            product.save()
        
        return product
