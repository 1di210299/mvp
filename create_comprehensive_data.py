#!/usr/bin/env python
"""
Script para crear datos completos y realistas para MVP profesional
Incluye datos históricos, transacciones, reportes, forecasting, etc.
"""
import os
import sys
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import Company
from inventory.models import (
    Category, Supplier, Product, Customer, Lead, Location, 
    InventoryItem, Transaction, Sale, Alert, InventoryHistory
)

User = get_user_model()

def create_comprehensive_mvp_data():
    """Crear dataset completo para MVP profesional"""
    print("🚀 Creando dataset completo para MVP...")
    
    # 1. EMPRESA PRINCIPAL
    company, created = Company.objects.get_or_create(
        name='Distribuidora San Martín SAC',
        defaults={
            'ruc': '20123456789',
            'address': 'Av. San Martín 1234, Lima Centro, Lima 15001, Perú',
            'phone': '+51 1 234-5678',
            'email': 'info@distribuidorasanmartin.com.pe',
            'industry': 'Distribución de productos de consumo masivo',
            'is_active': True,
            'website': 'www.distribuidorasanmartin.com.pe'
        }
    )
    print(f"✅ Empresa: {company.name}")
    
    # 2. CATEGORÍAS COMPLETAS
    categories_data = [
        {'name': 'Abarrotes', 'description': 'Productos de primera necesidad como arroz, aceite, azúcar'},
        {'name': 'Bebidas', 'description': 'Gaseosas, jugos, agua, bebidas energizantes'},
        {'name': 'Lácteos', 'description': 'Leche, quesos, yogures, mantequilla'},
        {'name': 'Panadería', 'description': 'Pan, galletas, productos de panadería'},
        {'name': 'Limpieza', 'description': 'Detergentes, jabones, productos de limpieza'},
        {'name': 'Cuidado Personal', 'description': 'Champú, pasta dental, jabón corporal'},
        {'name': 'Snacks', 'description': 'Galletas, chocolates, dulces, bocaditos'},
        {'name': 'Congelados', 'description': 'Helados, hamburguesas, nuggets'},
        {'name': 'Cereales', 'description': 'Cereales para desayuno, avena, granola'},
        {'name': 'Conservas', 'description': 'Atún, sardinas, duraznos en almíbar'},
        {'name': 'Condimentos', 'description': 'Sal, pimienta, ají, especias'},
        {'name': 'Bebidas Alcohólicas', 'description': 'Cerveza, vino, pisco'},
    ]
    
    categories = {}
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        categories[cat_data['name']] = category
    print(f"✅ Categorías: {len(categories)}")
    
    # 3. PROVEEDORES PERUANOS REALES
    suppliers_data = [
        {
            'name': 'Gloria S.A.',
            'contact_name': 'Carlos Mendoza Rivera',
            'email': 'ventas@gloria.com.pe',
            'phone': '+51 1 345-6789',
            'address': 'Av. República de Panamá 2461, La Victoria',
            'city': 'Lima',
            'country': 'Perú',
            'tax_id': '20100190797',
            'payment_terms': '30 días'
        },
        {
            'name': 'Alicorp S.A.A.',
            'contact_name': 'María González Vega',
            'email': 'comercial@alicorp.com.pe',
            'phone': '+51 1 456-7890',
            'address': 'Av. Argentina 4793, Callao',
            'city': 'Lima',
            'country': 'Perú',
            'tax_id': '20100055237',
            'payment_terms': '45 días'
        },
        {
            'name': 'Coca Cola Perú S.A.',
            'contact_name': 'Luis Ramírez Torres',
            'email': 'ventas@cocacola.com.pe',
            'phone': '+51 1 567-8901',
            'address': 'Av. Nicolás Ayllón 3986, Ate',
            'city': 'Lima',
            'country': 'Perú',
            'tax_id': '20100113610',
            'payment_terms': '30 días'
        },
        {
            'name': 'Nestlé Perú S.A.',
            'contact_name': 'Ana Torres Morales',
            'email': 'ventas@nestle.com.pe',
            'phone': '+51 1 678-9012',
            'address': 'Av. Santo Toribio 143, San Isidro',
            'city': 'Lima',
            'country': 'Perú',
            'tax_id': '20100166594',
            'payment_terms': '30 días'
        },
        {
            'name': 'Grupo Bimbo Perú S.A.',
            'contact_name': 'Pedro Silva Castillo',
            'email': 'ventas@bimbo.com.pe',
            'phone': '+51 1 789-0123',
            'address': 'Av. Los Frutales 220, Ate',
            'city': 'Lima',
            'country': 'Perú',
            'tax_id': '20100123456',
            'payment_terms': '15 días'
        },
        {
            'name': 'Unilever Andina Perú S.A.',
            'contact_name': 'Carmen Ruiz López',
            'email': 'comercial@unilever.com.pe',
            'phone': '+51 1 890-1234',
            'address': 'Av. Caminos del Inca 385, Santiago de Surco',
            'city': 'Lima',
            'country': 'Perú',
            'tax_id': '20100789012',
            'payment_terms': '45 días'
        }
    ]
    
    suppliers = {}
    for sup_data in suppliers_data:
        supplier, created = Supplier.objects.get_or_create(
            name=sup_data['name'],
            defaults=sup_data
        )
        suppliers[sup_data['name']] = supplier
    print(f"✅ Proveedores: {len(suppliers)}")
    
    # 4. UBICACIONES/ALMACENES
    locations_data = [
        {
            'name': 'Almacén Principal Lima Centro',
            'code': 'ALM-LC-01',
            'description': 'Almacén principal en Lima Centro',
            'warehouse': 'Lima Centro',
            'zone': 'A',
            'aisle': '01',
            'rack': '01',
            'shelf': '01'
        },
        {
            'name': 'Almacén Lima Norte',
            'code': 'ALM-LN-02',
            'description': 'Almacén secundario en Lima Norte',
            'warehouse': 'Lima Norte',
            'zone': 'B',
            'aisle': '02',
            'rack': '01',
            'shelf': '01'
        },
        {
            'name': 'Cámara Refrigerada',
            'code': 'REF-01',
            'description': 'Almacén refrigerado para lácteos',
            'warehouse': 'Lima Centro',
            'zone': 'C',
            'aisle': '03',
            'rack': '01',
            'shelf': '01'
        },
        {
            'name': 'Almacén Callao',
            'code': 'ALM-CA-03',
            'description': 'Almacén en el Callao cerca del puerto',
            'warehouse': 'Callao',
            'zone': 'D',
            'aisle': '04',
            'rack': '01',
            'shelf': '01'
        }
    ]
    
    locations = {}
    for loc_data in locations_data:
        location, created = Location.objects.get_or_create(
            code=loc_data['code'],
            defaults=loc_data
        )
        locations[loc_data['name']] = location
    print(f"✅ Ubicaciones: {len(locations)}")
    
    # 5. PRODUCTOS PERUANOS REALISTAS (50+ productos)
    products_data = [
        # LÁCTEOS GLORIA
        {'name': 'Leche Gloria Entera 1L', 'sku': 'LAC-001', 'category': 'Lácteos', 'supplier': 'Gloria S.A.', 'cost_price': 3.20, 'sale_price': 4.50, 'stock': 120, 'min_stock': 20, 'max_stock': 200, 'barcode': '7751271000123'},
        {'name': 'Leche Gloria Descremada 1L', 'sku': 'LAC-002', 'category': 'Lácteos', 'supplier': 'Gloria S.A.', 'cost_price': 3.30, 'sale_price': 4.70, 'stock': 85, 'min_stock': 15, 'max_stock': 180, 'barcode': '7751271000124'},
        {'name': 'Yogurt Gloria Fresa 1L', 'sku': 'LAC-003', 'category': 'Lácteos', 'supplier': 'Gloria S.A.', 'cost_price': 5.20, 'sale_price': 7.50, 'stock': 45, 'min_stock': 10, 'max_stock': 100, 'barcode': '7751271000125'},
        {'name': 'Queso Bonlé Edam 250g', 'sku': 'LAC-004', 'category': 'Lácteos', 'supplier': 'Gloria S.A.', 'cost_price': 8.50, 'sale_price': 12.90, 'stock': 35, 'min_stock': 8, 'max_stock': 80, 'barcode': '7751271000126'},
        
        # ABARROTES ALICORP
        {'name': 'Aceite Primor 1L', 'sku': 'ABA-001', 'category': 'Abarrotes', 'supplier': 'Alicorp S.A.A.', 'cost_price': 8.50, 'sale_price': 12.00, 'stock': 80, 'min_stock': 15, 'max_stock': 150, 'barcode': '7751271000201'},
        {'name': 'Fideos Don Vittorio Spaghetti 500g', 'sku': 'ABA-002', 'category': 'Abarrotes', 'supplier': 'Alicorp S.A.A.', 'cost_price': 2.80, 'sale_price': 4.20, 'stock': 180, 'min_stock': 40, 'max_stock': 250, 'barcode': '7751271000202'},
        {'name': 'Harina Blanca Flor 1kg', 'sku': 'ABA-003', 'category': 'Abarrotes', 'supplier': 'Alicorp S.A.A.', 'cost_price': 3.10, 'sale_price': 4.80, 'stock': 95, 'min_stock': 20, 'max_stock': 180, 'barcode': '7751271000203'},
        {'name': 'Detergente Ariel 780g', 'sku': 'LIM-001', 'category': 'Limpieza', 'supplier': 'Alicorp S.A.A.', 'cost_price': 12.50, 'sale_price': 18.90, 'stock': 60, 'min_stock': 15, 'max_stock': 120, 'barcode': '7751271000301'},
        
        # BEBIDAS COCA COLA
        {'name': 'Coca Cola 2L', 'sku': 'BEB-001', 'category': 'Bebidas', 'supplier': 'Coca Cola Perú S.A.', 'cost_price': 4.80, 'sale_price': 7.00, 'stock': 150, 'min_stock': 30, 'max_stock': 250, 'barcode': '7751271000401'},
        {'name': 'Sprite 2L', 'sku': 'BEB-002', 'category': 'Bebidas', 'supplier': 'Coca Cola Perú S.A.', 'cost_price': 4.60, 'sale_price': 6.80, 'stock': 120, 'min_stock': 25, 'max_stock': 200, 'barcode': '7751271000402'},
        {'name': 'Inca Kola 2L', 'sku': 'BEB-003', 'category': 'Bebidas', 'supplier': 'Coca Cola Perú S.A.', 'cost_price': 4.90, 'sale_price': 7.20, 'stock': 110, 'min_stock': 20, 'max_stock': 180, 'barcode': '7751271000403'},
        {'name': 'Agua San Luis 625ml', 'sku': 'BEB-004', 'category': 'Bebidas', 'supplier': 'Coca Cola Perú S.A.', 'cost_price': 1.20, 'sale_price': 2.00, 'stock': 300, 'min_stock': 100, 'max_stock': 500, 'barcode': '7751271000404'},
        
        # NESTLÉ
        {'name': 'Maggi Cubito Gallina 8und', 'sku': 'CON-001', 'category': 'Condimentos', 'supplier': 'Nestlé Perú S.A.', 'cost_price': 2.10, 'sale_price': 3.50, 'stock': 200, 'min_stock': 50, 'max_stock': 300, 'barcode': '7751271000501'},
        {'name': 'Nescafé Clásico 170g', 'sku': 'BEB-005', 'category': 'Bebidas', 'supplier': 'Nestlé Perú S.A.', 'cost_price': 18.50, 'sale_price': 25.90, 'stock': 45, 'min_stock': 10, 'max_stock': 90, 'barcode': '7751271000502'},
        {'name': 'Cerelac Trigo 400g', 'sku': 'CER-001', 'category': 'Cereales', 'supplier': 'Nestlé Perú S.A.', 'cost_price': 12.80, 'sale_price': 18.50, 'stock': 25, 'min_stock': 5, 'max_stock': 60, 'barcode': '7751271000503'},
        {'name': 'Sublime Clásico 30g', 'sku': 'SNK-001', 'category': 'Snacks', 'supplier': 'Nestlé Perú S.A.', 'cost_price': 1.50, 'sale_price': 2.50, 'stock': 180, 'min_stock': 50, 'max_stock': 300, 'barcode': '7751271000504'},
        
        # BIMBO
        {'name': 'Pan Bimbo Grande', 'sku': 'PAN-001', 'category': 'Panadería', 'supplier': 'Grupo Bimbo Perú S.A.', 'cost_price': 3.80, 'sale_price': 5.50, 'stock': 65, 'min_stock': 20, 'max_stock': 120, 'barcode': '7751271000601'},
        {'name': 'Pan Bimbo Integral', 'sku': 'PAN-002', 'category': 'Panadería', 'supplier': 'Grupo Bimbo Perú S.A.', 'cost_price': 4.20, 'sale_price': 6.00, 'stock': 50, 'min_stock': 15, 'max_stock': 100, 'barcode': '7751271000602'},
        {'name': 'Donuts Bimbo x6', 'sku': 'SNK-002', 'category': 'Snacks', 'supplier': 'Grupo Bimbo Perú S.A.', 'cost_price': 6.50, 'sale_price': 9.50, 'stock': 40, 'min_stock': 12, 'max_stock': 80, 'barcode': '7751271000603'},
        
        # UNILEVER
        {'name': 'Shampu Sedal 340ml', 'sku': 'CUI-001', 'category': 'Cuidado Personal', 'supplier': 'Unilever Andina Perú S.A.', 'cost_price': 8.20, 'sale_price': 12.50, 'stock': 70, 'min_stock': 15, 'max_stock': 140, 'barcode': '7751271000701'},
        {'name': 'Jabón Dove 90g', 'sku': 'CUI-002', 'category': 'Cuidado Personal', 'supplier': 'Unilever Andina Perú S.A.', 'cost_price': 3.80, 'sale_price': 6.20, 'stock': 90, 'min_stock': 20, 'max_stock': 160, 'barcode': '7751271000702'},
        {'name': 'Pasta Dental Close Up 60ml', 'sku': 'CUI-003', 'category': 'Cuidado Personal', 'supplier': 'Unilever Andina Perú S.A.', 'cost_price': 4.50, 'sale_price': 7.20, 'stock': 55, 'min_stock': 15, 'max_stock': 110, 'barcode': '7751271000703'},
        
        # PRODUCTOS ADICIONALES PARA COMPLETAR
        {'name': 'Arroz Superior Extra 5kg', 'sku': 'ABA-004', 'category': 'Abarrotes', 'supplier': 'Alicorp S.A.A.', 'cost_price': 15.80, 'sale_price': 22.50, 'stock': 40, 'min_stock': 10, 'max_stock': 80, 'barcode': '7751271000801'},
        {'name': 'Azúcar Rubia 1kg', 'sku': 'ABA-005', 'category': 'Abarrotes', 'supplier': 'Gloria S.A.', 'cost_price': 3.20, 'sale_price': 5.00, 'stock': 85, 'min_stock': 20, 'max_stock': 150, 'barcode': '7751271000802'},
        {'name': 'Atún Florida en Aceite 170g', 'sku': 'CON-002', 'category': 'Conservas', 'supplier': 'Alicorp S.A.A.', 'cost_price': 4.80, 'sale_price': 7.50, 'stock': 95, 'min_stock': 25, 'max_stock': 180, 'barcode': '7751271000803'},
        {'name': 'Galletas Oreo 432g', 'sku': 'SNK-003', 'category': 'Snacks', 'supplier': 'Nestlé Perú S.A.', 'cost_price': 6.80, 'sale_price': 9.50, 'stock': 30, 'min_stock': 8, 'max_stock': 70, 'barcode': '7751271000804'},
        {'name': 'Cerveza Pilsen 330ml x6', 'sku': 'ALC-001', 'category': 'Bebidas Alcohólicas', 'supplier': 'Alicorp S.A.A.', 'cost_price': 18.50, 'sale_price': 26.00, 'stock': 60, 'min_stock': 15, 'max_stock': 120, 'barcode': '7751271000805'},
    ]
    
    products = {}
    for prod_data in products_data:
        product_data = {
            'name': prod_data['name'],
            'sku': prod_data['sku'],
            'description': f"Producto {prod_data['name']} de alta calidad",
            'category': categories[prod_data['category']],
            'supplier': suppliers[prod_data['supplier']],
            'company': company,
            'cost_price': Decimal(str(prod_data['cost_price'])),
            'sale_price': Decimal(str(prod_data['sale_price'])),
            'price': Decimal(str(prod_data['sale_price'])),
            'stock': prod_data['stock'],
            'min_stock': prod_data['min_stock'],
            'max_stock': prod_data['max_stock'],
            'unit': 'unidad',
            'barcode': prod_data['barcode'],
            'weight': Decimal(str(random.uniform(0.1, 2.5))),
            'is_active': True
        }
        
        product, created = Product.objects.get_or_create(
            sku=prod_data['sku'],
            defaults=product_data
        )
        products[prod_data['name']] = product
    print(f"✅ Productos: {len(products)}")
    
    # 6. CLIENTES REALISTAS
    customers_data = [
        {
            'name': 'Bodega San Pedro',
            'email': 'pedidos@bodegasanpedro.com',
            'phone': '+51 1 789-0123',
            'address': 'Jr. San Pedro 456, Breña',
            'city': 'Lima',
            'tax_id': '10123456789',
            'customer_type': 'business',
            'credit_limit': Decimal('5000.00')
        },
        {
            'name': 'Minimarket El Dorado',
            'email': 'compras@eldorado.com',
            'phone': '+51 1 890-1234',
            'address': 'Av. El Dorado 789, San Juan de Lurigancho',
            'city': 'Lima',
            'tax_id': '20234567890',
            'customer_type': 'business',
            'credit_limit': Decimal('8000.00')
        },
        {
            'name': 'Supermercado La Familia',
            'email': 'ventas@lafamilia.com',
            'phone': '+51 1 567-8910',
            'address': 'Av. La Marina 1234, San Miguel',
            'city': 'Lima',
            'tax_id': '20345678901',
            'customer_type': 'business',
            'credit_limit': Decimal('12000.00')
        },
        {
            'name': 'Juan Carlos Pérez',
            'email': 'jcperez@email.com',
            'phone': '+51 987 654 321',
            'address': 'Calle Los Olivos 123, Miraflores',
            'city': 'Lima',
            'tax_id': '12345678',
            'customer_type': 'individual',
            'credit_limit': Decimal('1000.00')
        },
        {
            'name': 'María Elena Gonzales',
            'email': 'maria.gonzales@gmail.com',
            'phone': '+51 987 123 456',
            'address': 'Jr. Los Cedros 789, San Borja',
            'city': 'Lima',
            'tax_id': '23456789',
            'customer_type': 'individual',
            'credit_limit': Decimal('800.00')
        },
        {
            'name': 'Distribuidora Norte SAC',
            'email': 'ventas@distribuidoranorte.com',
            'phone': '+51 1 456-7890',
            'address': 'Av. Túpac Amaru 2456, Independencia',
            'city': 'Lima',
            'tax_id': '20456789012',
            'customer_type': 'business',
            'credit_limit': Decimal('15000.00')
        }
    ]
    
    customers = {}
    for cust_data in customers_data:
        customer, created = Customer.objects.get_or_create(
            tax_id=cust_data['tax_id'],
            defaults=cust_data
        )
        customers[cust_data['name']] = customer
    print(f"✅ Clientes: {len(customers)}")
    
    # 7. LEADS/PROSPECTOS
    user = User.objects.first()
    leads_data = [
        {
            'name': 'Roberto Martínez',
            'email': 'roberto.martinez@bodegacentral.com',
            'phone': '+51 987 234 567',
            'company': 'Bodega Central',
            'source': 'web',
            'status': 'new',
            'estimated_value': Decimal('3000.00'),
            'notes': 'Interesado en productos lácteos y abarrotes',
            'assigned_to': user,
            'expected_close_date': timezone.now().date() + timedelta(days=15)
        },
        {
            'name': 'Carmen Rodriguez',
            'email': 'c.rodriguez@minimarket.com',
            'phone': '+51 976 543 210',
            'company': 'Minimarket Rodriguez',
            'source': 'referral',
            'status': 'qualified',
            'estimated_value': Decimal('5000.00'),
            'notes': 'Busca proveedor regular de bebidas',
            'assigned_to': user,
            'expected_close_date': timezone.now().date() + timedelta(days=10)
        },
        {
            'name': 'Luis Alberto Torres',
            'email': 'l.torres@superperu.com',
            'phone': '+51 965 432 109',
            'company': 'Super Perú',
            'source': 'phone',
            'status': 'proposal',
            'estimated_value': Decimal('8500.00'),
            'notes': 'Cadena de supermercados, necesita variedad',
            'assigned_to': user,
            'expected_close_date': timezone.now().date() + timedelta(days=7)
        },
        {
            'name': 'Ana María Vega',
            'email': 'anavega@distribuidorasur.com',
            'phone': '+51 954 321 098',
            'company': 'Distribuidora Sur',
            'source': 'social',
            'status': 'negotiation',
            'estimated_value': Decimal('12000.00'),
            'notes': 'Distribuidora establecida, quiere ampliar catálogo',
            'assigned_to': user,
            'expected_close_date': timezone.now().date() + timedelta(days=5)
        },
        {
            'name': 'Pedro Castillo Silva',
            'email': 'pcastillo@megamercado.com',
            'phone': '+51 943 210 987',
            'company': 'Mega Mercado',
            'source': 'email',
            'status': 'contacted',
            'estimated_value': Decimal('6500.00'),
            'notes': 'Interesado en productos de limpieza',
            'assigned_to': user,
            'expected_close_date': timezone.now().date() + timedelta(days=20)
        }
    ]
    
    leads = {}
    for lead_data in leads_data:
        lead, created = Lead.objects.get_or_create(
            email=lead_data['email'],
            defaults=lead_data
        )
        # Asignar productos de interés aleatoriamente
        if created:
            interested_products = random.sample(list(products.values()), k=random.randint(2, 5))
            lead.interested_products.set(interested_products)
        leads[lead_data['name']] = lead
    print(f"✅ Leads: {len(leads)}")
    
    # 8. VENTAS HISTÓRICAS (últimos 3 meses)
    sales_count = 0
    start_date = timezone.now() - timedelta(days=90)
    
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        
        # 2-5 ventas por día
        daily_sales = random.randint(2, 5)
        
        for sale_num in range(daily_sales):
            product = random.choice(list(products.values()))
            customer = random.choice(list(customers.values()))
            quantity = random.randint(1, 20)
            
            # Variación de precio ±10%
            base_price = product.sale_price
            price_variation = random.uniform(0.9, 1.1)
            unit_price = base_price * Decimal(str(price_variation))
            
            Sale.objects.get_or_create(
                product=product,
                customer_name=customer.name,
                date_sold=current_date - timedelta(hours=random.randint(0, 23)),
                defaults={
                    'quantity': quantity,
                    'unit_price': unit_price.quantize(Decimal('0.01')),
                }
            )
            sales_count += 1
    print(f"✅ Ventas históricas: {sales_count}")
    
    # 9. TRANSACCIONES DE INVENTARIO
    transactions_count = 0
    
    for product in list(products.values())[:15]:  # Solo para algunos productos
        for location in list(locations.values())[:2]:  # Solo principales
            # Transacciones de entrada (compras)
            for i in range(random.randint(3, 8)):
                Transaction.objects.get_or_create(
                    product=product,
                    location=location,
                    transaction_type='purchase',
                    quantity=Decimal(str(random.randint(50, 200))),
                    unit_cost=product.cost_price,
                    reference_number=f'COMP-{random.randint(1000, 9999)}',
                    notes='Compra a proveedor',
                    defaults={
                        'transaction_date': timezone.now() - timedelta(days=random.randint(1, 60)),
                        'created_by': user
                    }
                )
                transactions_count += 1
            
            # Transacciones de salida (ventas)
            for i in range(random.randint(5, 12)):
                Transaction.objects.get_or_create(
                    product=product,
                    location=location,
                    transaction_type='sale',
                    quantity=Decimal(str(-random.randint(5, 30))),
                    reference_number=f'VENT-{random.randint(1000, 9999)}',
                    notes='Venta a cliente',
                    defaults={
                        'transaction_date': timezone.now() - timedelta(days=random.randint(1, 30)),
                        'created_by': user
                    }
                )
                transactions_count += 1
    print(f"✅ Transacciones: {transactions_count}")
    
    # 10. ITEMS DE INVENTARIO POR UBICACIÓN
    inventory_items_count = 0
    for product in products.values():
        for location in locations.values():
            # Distribuir stock entre ubicaciones
            if location.code == 'ALM-LC-01':  # Principal
                quantity = int(product.stock * 0.5)
            elif location.code == 'ALM-LN-02':  # Secundario
                quantity = int(product.stock * 0.3)
            elif location.code == 'REF-01':  # Refrigerado
                quantity = int(product.stock * 0.15) if product.category.name == 'Lácteos' else 0
            else:  # Callao
                quantity = int(product.stock * 0.05)
            
            if quantity > 0:
                InventoryItem.objects.get_or_create(
                    product=product,
                    location=location,
                    defaults={
                        'quantity': Decimal(str(quantity)),
                        'unit_cost': product.cost_price,
                        'batch_number': f'LOTE-{product.sku[-3:]}-{location.code[-2:]}-{random.randint(100, 999)}',
                        'manufacturing_date': timezone.now().date() - timedelta(days=random.randint(30, 180)),
                        'expiration_date': timezone.now().date() + timedelta(days=random.randint(180, 730)) if product.category.name in ['Lácteos', 'Conservas'] else None
                    }
                )
                inventory_items_count += 1
    print(f"✅ Items de inventario: {inventory_items_count}")
    
    # 11. ALERTAS DE STOCK Y OTROS
    alerts_count = 0
    
    # Alertas de stock bajo
    for product in products.values():
        if product.stock <= product.min_stock:
            Alert.objects.get_or_create(
                product=product,
                defaults={
                    'message': f'Stock bajo para {product.name}. Stock actual: {product.stock}, mínimo: {product.min_stock}',
                    'severity': 'high' if product.stock < product.min_stock * 0.5 else 'medium',
                    'is_active': True
                }
            )
            alerts_count += 1
    
    # Alertas de productos por vencer (si aplicable)
    for item in InventoryItem.objects.filter(expiration_date__isnull=False):
        days_to_expire = (item.expiration_date - timezone.now().date()).days
        if days_to_expire <= 30:
            Alert.objects.get_or_create(
                product=item.product,
                message=f'Producto {item.product.name} próximo a vencer en {days_to_expire} días',
                defaults={
                    'severity': 'high' if days_to_expire <= 7 else 'medium',
                    'is_active': True
                }
            )
            alerts_count += 1
    
    print(f"✅ Alertas: {alerts_count}")
    
    # 12. HISTORIAL DE INVENTARIO
    history_count = 0
    for product in list(products.values())[:10]:  # Solo algunos productos
        for i in range(random.randint(5, 15)):
            old_stock = random.randint(50, 200)
            new_stock = old_stock + random.randint(-30, 50)
            
            InventoryHistory.objects.get_or_create(
                product=product,
                stock_before=old_stock,
                stock_after=new_stock,
                change_reason=random.choice(['Venta', 'Compra', 'Ajuste', 'Devolución', 'Merma']),
                defaults={
                    'date_changed': timezone.now() - timedelta(days=random.randint(1, 60)),
                    'user': user
                }
            )
            history_count += 1
    print(f"✅ Historial de inventario: {history_count}")
    
    print("\n🎉 ¡Dataset completo para MVP creado exitosamente!")
    print(f"📊 RESUMEN COMPLETO:")
    print(f"   🏢 Empresa: {company.name}")
    print(f"   📂 Categorías: {len(categories)}")
    print(f"   🏭 Proveedores: {len(suppliers)}")
    print(f"   📦 Productos: {len(products)}")
    print(f"   🏠 Ubicaciones: {len(locations)}")
    print(f"   👥 Clientes: {len(customers)}")
    print(f"   🎯 Leads: {len(leads)}")
    print(f"   💰 Ventas históricas: {sales_count}")
    print(f"   🔄 Transacciones: {transactions_count}")
    print(f"   📍 Items de inventario: {inventory_items_count}")
    print(f"   ⚠️  Alertas: {alerts_count}")
    print(f"   📈 Registros de historial: {history_count}")
    print(f"\n🔑 CREDENCIALES:")
    print(f"   📧 Email: superadmin@datalens.com")
    print(f"   🔒 Password: admin123")
    print(f"\n🌐 TU MVP ESTÁ LISTO:")
    print(f"   🎯 Frontend: http://localhost:8081")
    print(f"   🔧 Backend API: http://localhost:8080")
    print(f"   ⚙️ Admin Django: http://localhost:8080/admin")
    print(f"\n✨ Todas las páginas del frontend ahora tendrán datos realistas!")

if __name__ == '__main__':
    create_comprehensive_mvp_data()