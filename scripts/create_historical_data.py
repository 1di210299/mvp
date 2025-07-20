#!/usr/bin/env python3
"""
Script para crear datos históricos completos y realistas para el sistema DataLens
Basado en el análisis de la base de datos actual
"""

import os
import django
from datetime import datetime, timedelta, date
from decimal import Decimal
import random
import json
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from authentication.models import User, Company
from inventory.models import (
    Product, Category, Supplier, Location, Transaction, Sale, Lead, 
    Customer, InventoryItem, InventoryHistory, PurchaseOrder, Alert
)
from django.db import models

class HistoricalDataGenerator:
    def __init__(self):
        self.company = Company.objects.first()
        self.user = User.objects.first()
        self.start_date = datetime.now() - timedelta(days=180)  # 6 meses atrás
        self.end_date = datetime.now()
        
        if not self.company or not self.user:
            raise Exception("❌ No se encontraron empresa o usuario. Ejecuta primero las migraciones.")
            
        print(f"🏢 Usando empresa: {self.company.name}")
        print(f"👤 Usando usuario: {self.user.email}")
        print(f"📅 Periodo: {self.start_date.strftime('%Y-%m-%d')} a {self.end_date.strftime('%Y-%m-%d')}")

    def create_base_data(self):
        """Crear datos base necesarios"""
        print("\n🏗️  CREANDO DATOS BASE...")
        
        # Categorías realistas
        categories_data = [
            ("Electrónicos", "Dispositivos electrónicos y tecnología"),
            ("Ropa y Accesorios", "Vestimenta y complementos"),
            ("Hogar y Jardín", "Artículos para el hogar"),
            ("Deportes y Fitness", "Equipos deportivos"),
            ("Salud y Belleza", "Productos de cuidado personal"),
            ("Oficina", "Suministros de oficina"),
            ("Automóvil", "Repuestos y accesorios"),
            ("Herramientas", "Herramientas y equipos"),
        ]
        
        self.categories = []
        for name, desc in categories_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc}
            )
            self.categories.append(category)
            print(f"  📂 Categoría: {name}")

        # Proveedores realistas
        suppliers_data = [
            ("TechGlobal SAC", "ventas@techglobal.pe", "+51 1 234-5678", "Jr. Tecnología 123, San Isidro"),
            ("Moda Lima EIRL", "pedidos@modalima.pe", "+51 1 345-6789", "Av. Moda 456, Miraflores"),
            ("Hogar Perú SA", "compras@hogarperu.pe", "+51 1 456-7890", "Calle Hogar 789, Surco"),
            ("Sports Center", "info@sportscenter.pe", "+51 1 567-8901", "Av. Deportes 321, La Molina"),
            ("Beauty Supply", "ventas@beautysupply.pe", "+51 1 678-9012", "Jr. Belleza 654, San Borja"),
            ("Oficina Total", "pedidos@oficinatotal.pe", "+51 1 789-0123", "Av. Oficina 987, Jesús María"),
            ("Auto Parts Lima", "ventas@autoparts.pe", "+51 1 890-1234", "Calle Auto 147, Lince"),
            ("Ferretería Industrial", "info@ferreteria.pe", "+51 1 901-2345", "Jr. Industria 258, Breña"),
        ]
        
        self.suppliers = []
        for name, email, phone, address in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=name,
                defaults={
                    'email': email,
                    'phone': phone,
                    'address': address,
                    'contact_name': f"Gerente de {name.split()[0]}"
                }
            )
            self.suppliers.append(supplier)
            print(f"  🏢 Proveedor: {name}")

        # Ubicaciones
        locations_data = [
            ("Almacén Principal", "ALM-01", "warehouse", "Av. Industrial 123, Ate"),
            ("Tienda Centro", "TDA-01", "store", "Jr. Unión 456, Cercado de Lima"),
            ("Tienda Norte", "TDA-02", "store", "Av. Tupac Amaru 789, Los Olivos"),
            ("Oficina Central", "OFC-01", "office", "Av. El Sol 321, San Isidro"),
        ]
        
        self.locations = []
        for name, code, warehouse, address in locations_data:
            location, created = Location.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'warehouse': warehouse,
                    'description': f"Ubicación {name}",
                    'zone': 'A',
                    'aisle': '1'
                }
            )
            self.locations.append(location)
            print(f"  📍 Ubicación: {name}")

        # Clientes
        customers_data = [
            ("Juan Pérez", "juan.perez@email.com", "+51 999 111 222", "individual"),
            ("María García", "maria.garcia@empresa.com", "+51 999 333 444", "business"),
            ("Carlos López", "carlos.lopez@negocio.pe", "+51 999 555 666", "business"),
            ("Ana Rodríguez", "ana.rodriguez@company.com", "+51 999 777 888", "individual"),
            ("Luis Martínez", "luis.martinez@corp.pe", "+51 999 999 000", "business"),
        ]
        
        self.customers = []
        for name, email, phone, customer_type in customers_data:
            customer, created = Customer.objects.get_or_create(
                email=email,
                defaults={
                    'name': name,
                    'phone': phone,
                    'customer_type': customer_type,
                    'address': f"Dirección de {name}",
                    'city': 'Lima'
                }
            )
            self.customers.append(customer)
            print(f"  👤 Cliente: {name}")

    def create_products(self):
        """Crear productos realistas con precios del mercado peruano"""
        print("\n📦 CREANDO PRODUCTOS...")
        
        products_data = [
            # Electrónicos
            ("Laptop HP Pavilion 15", "ELEC-001", 2200.00, 2800.00, 15, 5, 30, "Electrónicos"),
            ("Mouse Logitech MX", "ELEC-002", 85.00, 150.00, 45, 10, 80, "Electrónicos"),
            ("Teclado Mecánico RGB", "ELEC-003", 120.00, 220.00, 25, 8, 50, "Electrónicos"),
            ("Monitor 24\" Full HD", "ELEC-004", 480.00, 750.00, 12, 3, 25, "Electrónicos"),
            ("Smartphone Samsung A54", "ELEC-005", 980.00, 1350.00, 20, 5, 40, "Electrónicos"),
            ("Audífonos Sony WH-1000XM4", "ELEC-006", 780.00, 1100.00, 18, 5, 35, "Electrónicos"),
            ("Tablet iPad 9na Gen", "ELEC-007", 1250.00, 1680.00, 8, 2, 20, "Electrónicos"),
            ("Cámara Canon EOS M50", "ELEC-008", 1850.00, 2400.00, 5, 1, 15, "Electrónicos"),
            
            # Ropa y Accesorios
            ("Camisa Formal Blanca", "ROPA-001", 45.00, 85.00, 35, 8, 60, "Ropa y Accesorios"),
            ("Pantalón Jean Levis", "ROPA-002", 120.00, 189.00, 28, 6, 50, "Ropa y Accesorios"),
            ("Zapatos Clarks Desert", "ROPA-003", 280.00, 420.00, 15, 4, 30, "Ropa y Accesorios"),
            ("Reloj Casio G-Shock", "ROPA-004", 180.00, 280.00, 22, 5, 40, "Ropa y Accesorios"),
            ("Cartera de Cuero", "ROPA-005", 65.00, 120.00, 18, 5, 35, "Ropa y Accesorios"),
            ("Cinturón de Cuero", "ROPA-006", 35.00, 65.00, 25, 8, 45, "Ropa y Accesorios"),
            
            # Hogar y Jardín
            ("Aspiradora Electrolux", "HOGAR-001", 350.00, 550.00, 12, 3, 25, "Hogar y Jardín"),
            ("Microondas LG 20L", "HOGAR-002", 280.00, 420.00, 15, 4, 30, "Hogar y Jardín"),
            ("Licuadora Oster", "HOGAR-003", 85.00, 150.00, 20, 5, 40, "Hogar y Jardín"),
            ("Plancha Philips", "HOGAR-004", 45.00, 85.00, 30, 8, 50, "Hogar y Jardín"),
            ("Juego de Ollas Tramontina", "HOGAR-005", 180.00, 280.00, 10, 3, 20, "Hogar y Jardín"),
            ("Ventilador de Techo", "HOGAR-006", 120.00, 220.00, 8, 2, 18, "Hogar y Jardín"),
            
            # Deportes y Fitness
            ("Pelota de Fútbol Nike", "DEPORT-001", 45.00, 85.00, 35, 10, 60, "Deportes y Fitness"),
            ("Raqueta de Tenis Wilson", "DEPORT-002", 180.00, 320.00, 12, 3, 25, "Deportes y Fitness"),
            ("Pesas Mancuernas 10kg", "DEPORT-003", 85.00, 150.00, 15, 4, 30, "Deportes y Fitness"),
            ("Caminadora Eléctrica", "DEPORT-004", 1200.00, 1800.00, 3, 1, 8, "Deportes y Fitness"),
            ("Bicicleta Montañera", "DEPORT-005", 850.00, 1350.00, 6, 2, 12, "Deportes y Fitness"),
            
            # Salud y Belleza
            ("Crema Facial L'Oréal", "SALUD-001", 35.00, 65.00, 45, 12, 80, "Salud y Belleza"),
            ("Shampoo Pantene 400ml", "SALUD-002", 18.00, 35.00, 60, 15, 100, "Salud y Belleza"),
            ("Perfume Hugo Boss", "SALUD-003", 180.00, 320.00, 8, 2, 20, "Salud y Belleza"),
            ("Multivitamínico Centrum", "SALUD-004", 45.00, 85.00, 25, 8, 45, "Salud y Belleza"),
            
            # Oficina
            ("Impresora HP LaserJet", "OFIC-001", 380.00, 650.00, 8, 2, 18, "Oficina"),
            ("Silla Ergonómica", "OFIC-002", 220.00, 380.00, 12, 3, 25, "Oficina"),
            ("Escritorio de Madera", "OFIC-003", 320.00, 550.00, 6, 2, 15, "Oficina"),
            ("Calculadora Científica", "OFIC-004", 35.00, 65.00, 20, 5, 40, "Oficina"),
            
            # Automóvil
            ("Llantas Bridgestone 185/60R15", "AUTO-001", 180.00, 320.00, 16, 4, 32, "Automóvil"),
            ("Aceite Mobil 1 5W-30", "AUTO-002", 85.00, 150.00, 24, 6, 48, "Automóvil"),
            ("Batería Etna 12V", "AUTO-003", 220.00, 380.00, 8, 2, 20, "Automóvil"),
            ("Filtro de Aire Toyota", "AUTO-004", 35.00, 65.00, 30, 8, 60, "Automóvil"),
            
            # Herramientas
            ("Taladro Bosch Professional", "HERR-001", 280.00, 480.00, 10, 3, 20, "Herramientas"),
            ("Martillo Stanley 16oz", "HERR-002", 25.00, 45.00, 35, 10, 60, "Herramientas"),
            ("Destornillador Set 32 pcs", "HERR-003", 45.00, 85.00, 18, 5, 35, "Herramientas"),
            ("Sierra Circular Dewalt", "HERR-004", 420.00, 720.00, 5, 1, 12, "Herramientas"),
        ]
        
        self.products = []
        for name, sku, cost, sale, stock, min_stock, max_stock, cat_name in products_data:
            category = next((c for c in self.categories if c.name == cat_name), self.categories[0])
            supplier = random.choice(self.suppliers)
            
            product, created = Product.objects.get_or_create(
                sku=sku,
                company=self.company,
                defaults={
                    'name': name,
                    'category': category,
                    'supplier': supplier,
                    'cost_price': Decimal(str(cost)),
                    'sale_price': Decimal(str(sale)),
                    'stock': stock,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'unit': 'unidad',
                    'description': f"Producto de alta calidad - {name}",
                    'is_active': True
                }
            )
            self.products.append(product)
            if created:
                print(f"  ✅ {name} - S/ {cost} -> S/ {sale}")

        # Crear InventoryItems para cada producto en cada ubicación
        print("\n📦 Creando items de inventario...")
        for product in self.products:
            for location in self.locations[:2]:  # Solo almacén principal y tienda centro
                stock_distribution = {
                    "Almacén Principal": 0.7,  # 70% del stock
                    "Tienda Centro": 0.3       # 30% del stock
                }
                
                allocated_stock = int(product.stock * stock_distribution.get(location.name, 0))
                
                InventoryItem.objects.get_or_create(
                    product=product,
                    location=location,
                    defaults={
                        'quantity': allocated_stock,
                        'reserved_quantity': 0,
                        'unit_cost': product.cost_price
                    }
                )

    def create_historical_transactions(self):
        """Crear transacciones históricas realistas"""
        print("\n💰 CREANDO TRANSACCIONES HISTÓRICAS...")
        
        # Patrones estacionales (por mes)
        seasonal_patterns = {
            1: 0.8,   # Enero - bajo después de navidad
            2: 0.85,  # Febrero - San Valentín
            3: 0.9,   # Marzo - inicio de año
            4: 0.95,  # Abril - normal
            5: 1.0,   # Mayo - Día de la Madre
            6: 0.9,   # Junio - normal
            7: 1.1,   # Julio - Fiestas Patrias
            8: 0.95,  # Agosto - normal
            9: 1.0,   # Septiembre - vuelta a clases
            10: 1.05, # Octubre - preparación navidad
            11: 1.2,  # Noviembre - Black Friday
            12: 1.4   # Diciembre - Navidad
        }
        
        # Patrones por día de la semana
        weekly_patterns = {
            0: 0.8,   # Lunes
            1: 0.9,   # Martes
            2: 1.0,   # Miércoles
            3: 1.1,   # Jueves
            4: 1.3,   # Viernes
            5: 1.4,   # Sábado
            6: 0.7    # Domingo
        }
        
        current_date = self.start_date
        transaction_count = 0
        
        while current_date <= self.end_date:
            # Factores estacionales
            month_factor = seasonal_patterns.get(current_date.month, 1.0)
            weekday_factor = weekly_patterns.get(current_date.weekday(), 1.0)
            
            # Número base de transacciones por día (entre 5 y 25)
            base_transactions = random.randint(5, 25)
            daily_transactions = int(base_transactions * month_factor * weekday_factor)
            
            for _ in range(daily_transactions):
                # Tipo de transacción (más ventas que compras)
                transaction_type = random.choices(
                    ['sale', 'purchase', 'adjustment', 'return'],
                    weights=[70, 20, 5, 5]
                )[0]
                
                product = random.choice(self.products)
                location = random.choice(self.locations[:2])  # Solo almacén y tienda
                
                # Cantidad basada en el tipo de producto
                if product.category.name == "Electrónicos":
                    quantity = random.randint(1, 3)
                elif product.category.name == "Automóvil":
                    quantity = random.randint(1, 2)
                else:
                    quantity = random.randint(1, 8)
                
                # Precio con variación
                if transaction_type == 'sale':
                    base_price = product.sale_price
                    # Agregar descuentos ocasionales
                    if random.random() < 0.15:  # 15% chance de descuento
                        discount = Decimal(str(random.uniform(0.05, 0.20)))  # 5-20% descuento
                        unit_price = base_price * (Decimal('1') - discount)
                    else:
                        unit_price = base_price
                elif transaction_type == 'purchase':
                    unit_price = product.cost_price
                else:
                    unit_price = product.cost_price
                
                # Agregar variación de tiempo en el día
                hour = random.randint(8, 20)
                minute = random.randint(0, 59)
                transaction_datetime = current_date.replace(hour=hour, minute=minute)
                # Convertir a timezone aware
                transaction_datetime = timezone.make_aware(transaction_datetime)
                
                transaction = Transaction.objects.create(
                    product=product,
                    location=location,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    unit_cost=unit_price,
                    transaction_date=transaction_datetime,
                    notes=self.generate_transaction_note(transaction_type, product),
                    created_by=self.user
                )
                
                transaction_count += 1
                
                # Actualizar stock del producto (simulación básica)
                if transaction_type == 'sale' or transaction_type == 'return':
                    change = -quantity if transaction_type == 'sale' else quantity
                    product.stock = max(0, product.stock + change)
                elif transaction_type == 'purchase':
                    product.stock += quantity
                
                product.save()
            
            current_date += timedelta(days=1)
            
            # Progreso cada 30 días
            if (current_date - self.start_date).days % 30 == 0:
                print(f"  📅 Procesado hasta: {current_date.strftime('%Y-%m-%d')} - {transaction_count} transacciones")
        
        print(f"  ✅ Total transacciones creadas: {transaction_count}")

    def generate_transaction_note(self, transaction_type, product):
        """Generar notas realistas para transacciones"""
        notes = {
            'sale': [
                f"Venta directa - {product.name}",
                f"Venta mostrador - Cliente satisfecho",
                f"Venta online - Entrega programada",
                f"Venta corporativa - {product.name}",
                f"Promoción especial aplicada"
            ],
            'purchase': [
                f"Compra a proveedor - Restock {product.name}",
                f"Orden de compra completada",
                f"Reposición de inventario",
                f"Compra urgente - Stock bajo",
                f"Pedido programado mensual"
            ],
            'adjustment': [
                f"Ajuste de inventario - {product.name}",
                f"Corrección por diferencia física",
                f"Ajuste por daño menor",
                f"Actualización de stock"
            ],
            'return': [
                f"Devolución de cliente - {product.name}",
                f"Producto defectuoso devuelto",
                f"Cambio por garantía",
                f"Devolución por insatisfacción"
            ]
        }
        return random.choice(notes.get(transaction_type, ["Transacción procesada"]))

    def create_sales_records(self):
        """Crear registros de ventas detallados"""
        print("\n💳 CREANDO REGISTROS DE VENTAS...")
        
        sales_transactions = Transaction.objects.filter(transaction_type='sale')
        sales_count = 0
        
        for transaction in sales_transactions:
            # No todas las transacciones de venta tienen registro detallado
            if random.random() < 0.7:  # 70% de las ventas tienen registro detallado
                customer = random.choice(self.customers)
                
                Sale.objects.create(
                    product=transaction.product,
                    quantity=int(transaction.quantity),
                    unit_price=transaction.unit_cost,
                    customer_name=customer.name
                )
                sales_count += 1
        
        print(f"  ✅ Registros de ventas creados: {sales_count}")

    def create_leads(self):
        """Crear leads de ventas"""
        print("\n🎯 CREANDO LEADS DE VENTAS...")
        
        lead_sources = ['web', 'referral', 'social', 'email', 'phone', 'other']
        lead_statuses = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost']
        
        for _ in range(50):
            days_ago = random.randint(0, 180)
            created_date = self.end_date - timedelta(days=days_ago)
            
            status = random.choice(lead_statuses)
            estimated_value = random.uniform(100, 5000)
            
            lead = Lead.objects.create(
                name=f"Lead {random.randint(1000, 9999)}",
                email=f"lead{random.randint(100, 999)}@email.com",
                phone=f"+51 9{random.randint(10000000, 99999999)}",
                company=f"Empresa {random.randint(100, 999)} SAC",
                source=random.choice(lead_sources),
                status=status,
                estimated_value=Decimal(str(round(estimated_value, 2))),
                notes=f"Lead generado por {random.choice(['campaña digital', 'referido', 'visita web', 'llamada'])}",
                assigned_to=self.user
            )
            
            # Agregar productos de interés
            interested_products = random.sample(self.products, random.randint(1, 3))
            lead.interested_products.set(interested_products)
        
        print(f"  ✅ Leads creados: {Lead.objects.count()}")

    def create_purchase_orders(self):
        """Crear órdenes de compra"""
        print("\n📝 CREANDO ÓRDENES DE COMPRA...")
        
        statuses = ['draft', 'sent', 'confirmed', 'in_transit', 'received', 'cancelled']
        
        for i in range(30):
            product = random.choice(self.products)
            supplier = product.supplier
            quantity = random.randint(10, 100)
            
            days_ago = random.randint(0, 180)
            order_date = self.end_date - timedelta(days=days_ago)
            
            status = random.choice(statuses)
            
            # Fecha de entrega esperada
            expected_delivery = order_date + timedelta(days=random.randint(7, 30))
            
            # Generar número de orden único
            order_number = f"PO-{order_date.strftime('%Y%m%d')}-{i+1:03d}"
            
            PurchaseOrder.objects.create(
                order_number=order_number,
                company=self.company,
                product=product,
                supplier=supplier,
                quantity=quantity,
                unit_price=product.cost_price,
                total_amount=product.cost_price * quantity,
                status=status,
                expected_delivery_date=expected_delivery,
                notes=f"Orden de compra para restock - {product.name}",
                created_by=self.user
            )
        
        print(f"  ✅ Órdenes de compra creadas: {PurchaseOrder.objects.count()}")

    def create_alerts_and_rules(self):
        """Crear alertas y reglas de alerta"""
        print("\n🚨 CREANDO SISTEMA DE ALERTAS...")
        
        # Solo crear alertas simples basadas en el estado actual
        alert_count = 0
        for product in self.products:
            if product.stock <= product.min_stock:
                severity = 'high' if product.stock == 0 else 'medium'
                
                Alert.objects.get_or_create(
                    message=f"Stock bajo: {product.name}. Stock actual: {product.stock}, mínimo: {product.min_stock}",
                    product=product,
                    defaults={
                        'severity': severity,
                        'is_active': True
                    }
                )
                alert_count += 1
        
        print(f"  ✅ Alertas activas: {alert_count}")

    def create_intelligence_data(self):
        """Crear datos de inteligencia de negocio"""
        print("\n🧠 CREANDO DATOS DE INTELIGENCIA...")
        print("  ⚠️  Módulo de inteligencia no disponible en el modelo actual")

    def create_kpi_definitions(self):
        """Crear definiciones de KPIs"""
        print("\n📊 CREANDO DEFINICIONES DE KPIs...")
        print("  ⚠️  Módulo de KPIs no disponible en el modelo actual")

    def create_inventory_history(self):
        """Crear historial de cambios de inventario"""
        print("\n📋 CREANDO HISTORIAL DE INVENTARIO...")
        
        # Crear algunas entradas de historial para productos críticos
        products_with_low_stock = [p for p in self.products if p.stock <= p.min_stock]
        
        for product in products_with_low_stock[:10]:  # Solo los primeros 10
            for _ in range(random.randint(3, 8)):
                days_ago = random.randint(1, 60)
                change_date = self.end_date - timedelta(days=days_ago)
                
                change_type = random.choice(['sale', 'purchase', 'adjustment'])
                stock_before = random.randint(product.stock, product.stock + 20)
                
                if change_type == 'sale':
                    stock_after = stock_before - random.randint(1, 5)
                elif change_type == 'purchase':
                    stock_after = stock_before + random.randint(5, 20)
                else:
                    stock_after = stock_before + random.randint(-3, 3)
                
                stock_after = max(0, stock_after)
                
                InventoryHistory.objects.create(
                    product=product,
                    stock_before=stock_before,
                    stock_after=stock_after,
                    change_reason=f"Cambio por {change_type}",
                    user=self.user
                )
        
        print(f"  ✅ Historial de inventario: {InventoryHistory.objects.count()}")

    def generate_summary_report(self):
        """Generar reporte resumen de los datos creados"""
        print("\n" + "="*60)
        print("📊 RESUMEN FINAL DE DATOS HISTÓRICOS CREADOS")
        print("="*60)
        
        # Conteos
        print(f"🏢 Empresas: {Company.objects.count()}")
        print(f"👤 Usuarios: {User.objects.count()}")
        print(f"📂 Categorías: {Category.objects.count()}")
        print(f"🏭 Proveedores: {Supplier.objects.count()}")
        print(f"📍 Ubicaciones: {Location.objects.count()}")
        print(f"👥 Clientes: {Customer.objects.count()}")
        print(f"📦 Productos: {Product.objects.count()}")
        print(f"💰 Transacciones: {Transaction.objects.count()}")
        print(f"💳 Ventas detalladas: {Sale.objects.count()}")
        print(f"🎯 Leads: {Lead.objects.count()}")
        print(f"📝 Órdenes de compra: {PurchaseOrder.objects.count()}")
        print(f"🚨 Alertas: {Alert.objects.count()}")
        print(f" Historial inventario: {InventoryHistory.objects.count()}")
        
        # Cálculos de negocio
        print(f"\n💼 MÉTRICAS DE NEGOCIO:")
        
        # Ventas totales (basado en transacciones)
        sales_transactions = Transaction.objects.filter(transaction_type='sale')
        total_sales = sum(
            float(t.unit_cost) * float(t.quantity) for t in sales_transactions 
            if t.unit_cost and t.quantity
        )
        
        # Compras totales
        purchase_transactions = Transaction.objects.filter(transaction_type='purchase')
        total_purchases = sum(
            float(t.unit_cost) * float(t.quantity) for t in purchase_transactions 
            if t.unit_cost and t.quantity
        )
        
        # Valor de inventario
        inventory_value = sum(
            float(p.stock) * float(p.cost_price) for p in Product.objects.all() 
            if p.stock and p.cost_price
        )
        
        # Ventas últimos 30 días
        thirty_days_ago = self.end_date - timedelta(days=30)
        recent_sales_transactions = Transaction.objects.filter(
            transaction_type='sale',
            transaction_date__gte=thirty_days_ago
        )
        recent_sales = sum(
            float(t.unit_cost) * float(t.quantity) for t in recent_sales_transactions 
            if t.unit_cost and t.quantity
        )
        
        print(f"💰 Ventas totales (6 meses): S/ {total_sales:,.2f}")
        print(f"🛒 Compras totales (6 meses): S/ {total_purchases:,.2f}")
        print(f"💵 Ganancia bruta: S/ {total_sales - total_purchases:,.2f}")
        print(f"📦 Valor inventario actual: S/ {inventory_value:,.2f}")
        print(f"📈 Ventas últimos 30 días: S/ {recent_sales:,.2f}")
        print(f"🚨 Alertas activas: {Alert.objects.filter(is_active=True).count()}")
        
        # Productos top basado en transacciones
        product_sales = {}
        for transaction in sales_transactions:
            if transaction.product_id not in product_sales:
                product_sales[transaction.product_id] = 0
            product_sales[transaction.product_id] += float(transaction.unit_cost) * float(transaction.quantity)
        
        # Ordenar por ventas
        top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print(f"\n🏆 TOP 5 PRODUCTOS POR VENTAS:")
        for i, (product_id, total) in enumerate(top_products, 1):
            product = Product.objects.get(id=product_id)
            print(f"  {i}. {product.name}: S/ {total:,.2f}")
        
        print(f"\n🎉 ¡DATOS HISTÓRICOS CREADOS EXITOSAMENTE!")
        print(f"🌐 Dashboard actualizado: http://localhost:3000/app")
        print(f"⏰ Período de datos: {self.start_date.strftime('%Y-%m-%d')} a {self.end_date.strftime('%Y-%m-%d')}")

def main():
    """Función principal"""
    print("🚀 INICIANDO CREACIÓN DE DATOS HISTÓRICOS COMPLETOS...")
    print("="*60)
    
    try:
        generator = HistoricalDataGenerator()
        
        # Ejecutar en orden
        generator.create_base_data()
        generator.create_products()
        generator.create_historical_transactions()
        generator.create_sales_records()
        generator.create_leads()
        generator.create_purchase_orders()
        generator.create_alerts_and_rules()
        generator.create_intelligence_data()
        generator.create_kpi_definitions()
        generator.create_inventory_history()
        generator.generate_summary_report()
        
    except Exception as e:
        print(f"❌ Error durante la creación de datos: {str(e)}")
        raise

if __name__ == "__main__":
    main()
