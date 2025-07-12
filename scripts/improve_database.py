import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Detectar automáticamente el módulo de configuración de Django
def find_settings_module():
    """Encontrar el módulo de configuración de Django"""
    # Buscar directamente en el directorio del proyecto
    possible_settings = [
        project_root / 'inventory_system' / 'settings.py',
        project_root / 'mvp' / 'settings.py', 
        project_root / 'config' / 'settings.py',
        project_root / 'settings.py'
    ]
    
    for settings_path in possible_settings:
        if settings_path.exists():
            parent_name = settings_path.parent.name
            if parent_name == str(project_root.name):
                module_name = 'settings'
            else:
                module_name = f"{parent_name}.settings"
            
            try:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', module_name)
                import django
                django.setup()
                return module_name
            except Exception as e:
                print(f"Intentando {module_name}: {e}")
                continue
    
    # Método alternativo: buscar manage.py para inferir la estructura
    manage_py = project_root / 'manage.py'
    if manage_py.exists():
        with open(manage_py, 'r') as f:
            content = f.read()
            # Buscar la línea DJANGO_SETTINGS_MODULE
            for line in content.split('\n'):
                if 'DJANGO_SETTINGS_MODULE' in line and 'setdefault' in line:
                    # Extraer el módulo de configuración
                    import re
                    match = re.search(r"'([^']+)'", line)
                    if match:
                        module_name = match.group(1)
                        try:
                            os.environ.setdefault('DJANGO_SETTINGS_MODULE', module_name)
                            import django
                            django.setup()
                            return module_name
                        except:
                            continue
    
    return None

# Intentar configurar Django
django_configured = False
try:
    settings_module = find_settings_module()
    if settings_module:
        from inventory.models import Product
        from django.db import connection
        print(f"✅ Django configurado correctamente con {settings_module}")
        django_configured = True
    else:
        raise Exception("No se pudo encontrar el módulo de configuración")
        
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    print("📝 Continuando sin Django para actualizar modelos...")

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')

try:
    import django
    django.setup()
    
    from inventory.models import Product
    from django.db import connection
    
    print("✅ Django configurado correctamente")
    
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    print("📝 Vamos a crear los modelos directamente en inventory/models.py")
    
def fix_models_syntax():
    """Arreglar errores de sintaxis en models.py de forma más robusta"""
    models_file_path = project_root / 'inventory' / 'models.py'
    
    with open(models_file_path, 'r') as f:
        content = f.read()
    
    # Estrategia más agresiva: reescribir el archivo si hay problemas graves
    try:
        compile(content, models_file_path, 'exec')
        print("✅ Sintaxis del archivo models.py es correcta")
        return
    except SyntaxError as e:
        print(f"🔧 Reparando error de sintaxis en línea {e.lineno}")
    
    # Crear una versión limpia del archivo models.py
    clean_models = '''from django.db import models
from django.conf import settings

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    date_sold = models.DateTimeField(auto_now_add=True)
    customer_name = models.CharField(max_length=100, blank=True)
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Venta: {self.product.name} - {self.quantity} unidades"
    
    class Meta:
        ordering = ['-date_sold']

class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ]
    
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"Alerta {self.severity}: {self.message[:50]}"
    
    class Meta:
        ordering = ['-created_at']

class InventoryHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stock_before = models.IntegerField()
    stock_after = models.IntegerField()
    change_reason = models.CharField(max_length=100)
    date_changed = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.product.name}: {self.stock_before} -> {self.stock_after}"
    
    class Meta:
        ordering = ['-date_changed']
        verbose_name_plural = "Inventory Histories"
'''
    
    # Respaldar el archivo original
    backup_path = models_file_path.with_suffix('.py.backup')
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"📁 Respaldo creado en {backup_path}")
    
    # Escribir la versión limpia
    with open(models_file_path, 'w') as f:
        f.write(clean_models)
    
    print("✅ Archivo models.py reescrito con estructura limpia")

def update_models_file():
    """Agregar los nuevos modelos al archivo models.py existente"""
    
    models_file_path = project_root / 'inventory' / 'models.py'
    
    # Primero intentar arreglar errores de sintaxis
    try:
        fix_models_syntax()
    except Exception as e:
        print(f"⚠️ Advertencia al arreglar sintaxis: {e}")
    
    # Leer el contenido actual
    with open(models_file_path, 'r') as f:
        current_content = f.read()
    
    # Verificar si los modelos ya existen
    if 'class Sale(' not in current_content:
        # Nuevos modelos para agregar
        new_models = """

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    date_sold = models.DateTimeField(auto_now_add=True)
    customer_name = models.CharField(max_length=100, blank=True)
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Venta: {self.product.name} - {self.quantity} unidades"
    
    class Meta:
        ordering = ['-date_sold']


class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ]
    
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"Alerta {self.severity}: {self.message[:50]}"
    
    class Meta:
        ordering = ['-created_at']


class InventoryHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stock_before = models.IntegerField()
    stock_after = models.IntegerField()
    change_reason = models.CharField(max_length=100)
    date_changed = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.product.name}: {self.stock_before} -> {self.stock_after}"
    
    class Meta:
        ordering = ['-date_changed']
        verbose_name_plural = "Inventory Histories"
"""
        
        # Agregar los nuevos modelos al final del archivo
        updated_content = current_content + new_models
        
        # Escribir el archivo actualizado
        with open(models_file_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ Modelos agregados a inventory/models.py")
        print("📋 PASOS SIGUIENTES:")
        print("1. python manage.py makemigrations")
        print("2. python manage.py migrate")
        print("3. python scripts/improve_database.py (para generar datos de ejemplo)")
    else:
        print("ℹ️ Los modelos ya existen en inventory/models.py")
        # Verificar errores de sintaxis
        try:
            compile(current_content, models_file_path, 'exec')
            print("✅ Sintaxis del archivo models.py es correcta")
        except SyntaxError as e:
            print(f"❌ Error de sintaxis en models.py línea {e.lineno}: {e.msg}")
            print("🔧 Intentando reparar automáticamente...")
            fix_models_syntax()

def create_sample_data():
    """Crear datos de ejemplo para las nuevas tablas"""
    if not django_configured:
        print("❌ Django no está configurado. Ejecuta las migraciones primero.")
        return
        
    try:
        from inventory.models import Product, Sale, Alert, InventoryHistory
        from django.contrib.auth.models import User
        from datetime import datetime, timedelta
        import random
        from decimal import Decimal
        from django.db import models
        
        print("🔄 Generando datos de ejemplo...")
        
        # Verificar que los modelos existan
        try:
            Sale.objects.count()
        except Exception as e:
            print(f"❌ Los modelos no están migrados aún. Error: {e}")
            print("📋 Ejecuta: python manage.py makemigrations && python manage.py migrate")
            return
        
        # Obtener productos existentes
        products = list(Product.objects.all()[:20])
        if not products:
            print("❌ No hay productos en la base de datos. Agrega algunos productos primero.")
            return
        
        print(f"📦 Encontrados {len(products)} productos para generar datos")
        
        # Crear usuario de ejemplo si no existe
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True}
        )
        if created:
            user.set_password('admin123')
            user.save()
            print("👤 Usuario admin creado")
        
        # Limpiar datos existentes (opcional)
        existing_sales = Sale.objects.count()
        existing_alerts = Alert.objects.count()
        
        if existing_sales > 0 or existing_alerts > 0:
            print(f"📊 Datos existentes: {existing_sales} ventas, {existing_alerts} alertas")
            response = input("¿Quieres limpiar datos existentes? (y/N): ")
            if response.lower() == 'y':
                Sale.objects.all().delete()
                Alert.objects.all().delete()
                InventoryHistory.objects.all().delete()
                print("🗑️ Datos anteriores eliminados")
        
        # Generar ventas de ejemplo (últimos 60 días)
        sales_created = 0
        print("💰 Generando ventas...")
        
        for i in range(150):  # 150 ventas
            product = random.choice(products)
            quantity = random.randint(1, 8)
            # Precio con variación del ±20%
            base_price = float(product.price)
            variation = random.uniform(0.8, 1.2)
            unit_price = Decimal(str(base_price * variation))
            
            # Fecha aleatoria en los últimos 60 días
            days_ago = random.randint(0, 60)
            sale_date = datetime.now() - timedelta(days=days_ago)
            
            # Crear la venta
            Sale.objects.create(
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                customer_name=f"Cliente-{random.randint(1000, 9999)}",
                date_sold=sale_date
            )
            sales_created += 1
            
            if sales_created % 50 == 0:
                print(f"   ✅ {sales_created} ventas creadas...")
        
        # Generar alertas de ejemplo
        print("🚨 Generando alertas...")
        alerts_data = [
            ("Producto con stock crítico detectado en almacén principal", "high"),
            ("Revisión de inventario programada para mañana", "medium"),
            ("Nuevo lote de productos recibido correctamente", "low"),
            ("Stock repuesto automáticamente por el sistema", "low"),
            ("Producto próximo a fecha de vencimiento", "medium"),
            ("Alerta de stock bajo en productos de alta rotación", "high"),
            ("Mantenimiento del sistema de inventario completado", "low"),
        ]
        
        alerts_created = 0
        for message, severity in alerts_data:
            Alert.objects.create(
                message=message,
                severity=severity,
                product=random.choice(products) if random.choice([True, False]) else None
            )
            alerts_created += 1
        
        # Generar historial de inventario
        print("📝 Generando historial...")
        history_created = 0
        for product in products[:15]:  # Para 15 productos
            for i in range(random.randint(3, 7)):  # 3-7 cambios por producto
                days_ago = random.randint(1, 45)
                change_date = datetime.now() - timedelta(days=days_ago)
                
                stock_before = random.randint(5, 150)
                change = random.randint(-25, 40)
                stock_after = max(0, stock_before + change)
                
                reasons = [
                    "Venta al cliente", 
                    "Compra a proveedor", 
                    "Ajuste de inventario", 
                    "Devolución de cliente",
                    "Pérdida por daño",
                    "Transfer entre almacenes",
                    "Corrección manual"
                ]
                
                InventoryHistory.objects.create(
                    product=product,
                    stock_before=stock_before,
                    stock_after=stock_after,
                    change_reason=random.choice(reasons),
                    date_changed=change_date,
                    user=user
                )
                history_created += 1
        
        print(f"\n✅ Datos de ejemplo creados exitosamente:")
        print(f"   📊 {sales_created} ventas generadas")
        print(f"   🚨 {alerts_created} alertas creadas")
        print(f"   📝 {history_created} registros de historial")
        
        # Mostrar estadísticas finales
        total_sales = Sale.objects.count()
        total_revenue = Sale.objects.aggregate(total=models.Sum('total_amount'))['total'] or 0
        active_alerts = Alert.objects.filter(is_active=True).count()
        
        print(f"\n📈 Estadísticas finales del sistema:")
        print(f"   💰 Total ventas en BD: {total_sales}")
        print(f"   💵 Ingresos totales: ${total_revenue:,.2f}")
        print(f"   ⚠️ Alertas activas: {active_alerts}")
        print(f"   📦 Productos en sistema: {Product.objects.count()}")
        
    except ImportError as e:
        print(f"❌ Error: Los modelos no están disponibles. Ejecuta las migraciones primero.")
        print(f"   Detalle: {e}")
        print("📋 Comandos necesarios:")
        print("   1. python manage.py makemigrations")
        print("   2. python manage.py migrate")
    except Exception as e:
        print(f"❌ Error generando datos: {e}")
        import traceback
        traceback.print_exc()

def create_enhanced_api():
    """Crear una nueva vista para la API mejorada"""
    
    api_file_path = project_root / 'inventory' / 'enhanced_views.py'
    
    api_content = '''"""
Vistas mejoradas para reportes y analytics
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from inventory.models import Product, Sale, Alert, InventoryHistory
from decimal import Decimal

@api_view(['GET'])
def enhanced_reports_data(request):
    """API mejorada para reportes con datos reales"""
    try:
        # Métricas básicas
        total_products = Product.objects.count()
        total_inventory_value = Product.objects.aggregate(
            total=Sum(F('stock') * F('price'))
        )['total'] or 0
        
        # Ventas del mes actual
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        monthly_sales = Sale.objects.filter(date_sold__gte=current_month_start)
        
        sales_this_month = monthly_sales.aggregate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        # Productos más vendidos (últimos 30 días)
        last_30_days = datetime.now() - timedelta(days=30)
        top_products_data = Sale.objects.filter(date_sold__gte=last_30_days)\\
            .values('product__id', 'product__name', 'product__stock', 'product__price')\\
            .annotate(
                total_sold=Sum('quantity'),
                total_revenue=Sum('total_amount')
            )\\
            .order_by('-total_sold')[:10]
        
        # Alertas recientes activas
        recent_alerts = Alert.objects.filter(is_active=True).order_by('-created_at')[:10]
        
        # Datos mensuales para gráficos (últimos 12 meses)
        monthly_data = []
        for i in range(12):
            month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_sales = Sale.objects.filter(
                date_sold__gte=month_start,
                date_sold__lte=month_end
            ).aggregate(
                sales_count=Count('id'),
                revenue=Sum('total_amount'),
                units_sold=Sum('quantity')
            )
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'sales': month_sales['sales_count'] or 0,
                'inventory_value': float(total_inventory_value),
                'revenue': float(month_sales['revenue'] or 0),
                'units_sold': month_sales['units_sold'] or 0
            })
        
        monthly_data.reverse()  # Ordenar cronológicamente
        
        # Estado del inventario
        inventory_status = [
            {
                'status': 'En Stock',
                'count': Product.objects.filter(stock__gt=10).count(),
                'percentage': 0
            },
            {
                'status': 'Stock Bajo', 
                'count': Product.objects.filter(stock__lte=10, stock__gt=0).count(),
                'percentage': 0
            },
            {
                'status': 'Agotado',
                'count': Product.objects.filter(stock=0).count(),
                'percentage': 0
            }
        ]
        
        # Calcular porcentajes
        total_products_for_status = sum(item['count'] for item in inventory_status)
        if total_products_for_status > 0:
            for item in inventory_status:
                item['percentage'] = round((item['count'] / total_products_for_status) * 100, 1)
        
        return Response({
            'metrics': {
                'total_products': total_products,
                'total_inventory_value': float(total_inventory_value),
                'sales_this_month': sales_this_month['count'] or 0,
                'sales_value_this_month': float(sales_this_month['total'] or 0),
                'active_alerts': Alert.objects.filter(is_active=True).count(),
            },
            'trends': {
                'monthly_data': monthly_data,
                'inventory_status': inventory_status
            },
            'top_products': [
                {
                    'id': item['product__id'],
                    'name': item['product__name'],
                    'stock': item['product__stock'],
                    'price': float(item['product__price']),
                    'total_sold': item['total_sold'],
                    'total_revenue': float(item['total_revenue'] or 0)
                }
                for item in top_products_data
            ],
            'recent_alerts': [
                {
                    'id': alert.id,
                    'message': alert.message,
                    'severity': alert.severity,
                    'created_at': alert.created_at.isoformat(),
                    'product_name': alert.product.name if alert.product else None
                }
                for alert in recent_alerts
            ],
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': f'Error generando reportes: {str(e)}',
            'metrics': {
                'total_products': 0,
                'total_inventory_value': 0,
                'sales_this_month': 0,
                'sales_value_this_month': 0,
                'active_alerts': 0,
            },
            'trends': {'monthly_data': [], 'inventory_status': []},
            'top_products': [],
            'recent_alerts': [],
            'last_updated': datetime.now().isoformat()
        }, status=500)
'''
    
    # Escribir el archivo de API
    with open(api_file_path, 'w') as f:
        f.write(api_content)
    
    print("✅ API mejorada creada en inventory/enhanced_views.py")
    print("📋 Para usar la nueva API:")
    print("1. Agregar 'from inventory.enhanced_views import enhanced_reports_data' a urls.py")
    print("2. Agregar la ruta: path('api/enhanced-reports/', enhanced_reports_data)")

if __name__ == "__main__":
    print("🚀 Mejorando la base de datos para analytics...")
    
    # Primero arreglar cualquier problema de sintaxis
    print("🔧 Verificando sintaxis de models.py...")
    
    # Si Django está configurado, generar datos
    if django_configured:
        print("✅ Django configurado correctamente")
        create_sample_data()
    else:
        print("📝 Actualizando modelos...")
        update_models_file()
        print("\n📋 EJECUTA ESTOS COMANDOS EN ORDEN:")
        print("1. python manage.py makemigrations")
        print("2. python manage.py migrate")
        print("3. python scripts/improve_database.py")
    
    # Crear API mejorada siempre
    create_enhanced_api()
    
    print("\n🎯 PRÓXIMOS PASOS:")
    print("1. Ejecutar migraciones si no se han ejecutado")
    print("2. Actualizar urls.py con la nueva API")
    print("3. Actualizar el frontend para usar enhanced-reports")
