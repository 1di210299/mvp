#!/usr/bin/env python
"""
Script para crear datos completos y realistas para el sistema multi-tenant
ENFOQUE: Una empresa principal con datos completos + empresas adicionales para demostrar separación
"""
import os
import sys
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.contrib.auth.hashers import make_password

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import Company
from inventory.models import (
    Category, Supplier, Product, Customer, Lead, Location, 
    InventoryItem, Transaction, Sale, Alert, InventoryHistory
)
from forecasting.models import ForecastModel, DemandForecast, ReorderRecommendation

User = get_user_model()

def clear_existing_data():
    """Limpiar datos existentes de la base de datos"""
    print("🗑️ LIMPIANDO DATOS EXISTENTES...")
    
    # Orden importante para evitar errores de Foreign Key
    models_to_clear = [
        ReorderRecommendation,
        DemandForecast,
        ForecastModel,
        InventoryHistory,
        Alert,
        Sale,
        Transaction,
        InventoryItem,
        Lead,
        Customer,
        Product,
        Location,
        Supplier,
        Category,
        User,  # Excepto superuser
        Company
    ]
    
    for model in models_to_clear:
        if model == User:
            # Mantener superusuarios
            User.objects.filter(is_superuser=False).delete()
        else:
            model.objects.all().delete()
    
    print("✅ Datos existentes eliminados")

def create_main_company():
    """Crear la empresa principal con datos completos"""
    print("\n🏢 CREANDO EMPRESA PRINCIPAL...")
    
    company = Company.objects.create(
        name='Distribuidora San Martín SAC',
        ruc='20123456789',
        industry='Distribución de Alimentos y Bebidas',
        address='Av. Argentina 2845, Cercado de Lima, Lima',
        phone='+51-1-234-5678',
        email='contacto@sanmartin.com.pe',
        website='https://www.sanmartin.com.pe',
        subscription_type='premium',
        max_users=25,
        is_active=True
    )
    
    print(f"   ✅ {company.name} - RUC: {company.ruc}")
    return company

def create_demo_companies():
    """Crear empresas adicionales para demostrar separación multi-tenant"""
    print("\n🏭 CREANDO EMPRESAS DEMO...")
    
    demo_companies = []
    
    companies_data = [
        {
            'name': 'Comercial Norte EIRL',
            'ruc': '20234567890',
            'industry': 'Comercio al Por Mayor',
            'address': 'Jr. Ucayali 456, Trujillo, La Libertad',
            'phone': '+51-44-567-890',
            'email': 'ventas@comercialnorte.pe',
            'website': 'https://www.comercialnorte.pe',
            'subscription_type': 'basic',
            'max_users': 10
        },
        {
            'name': 'Supermercados El Ahorro SA',
            'ruc': '20345678901',
            'industry': 'Retail/Supermercados',
            'address': 'Av. Javier Prado 1234, San Isidro, Lima',
            'phone': '+51-1-345-6789',
            'email': 'info@elahorro.com.pe',
            'website': 'https://www.elahorro.com.pe',
            'subscription_type': 'premium',
            'max_users': 15
        }
    ]
    
    for company_data in companies_data:
        company = Company.objects.create(**company_data, is_active=True)
        demo_companies.append(company)
        print(f"   ✅ {company.name} - RUC: {company.ruc}")
    
    return demo_companies

def create_users_for_company(company, is_main=False):
    """Crear usuarios realistas para una empresa específica"""
    print(f"\n👥 CREANDO USUARIOS PARA {company.name}...")
    
    users = []
    
    # Admin principal de la empresa
    admin_user = User.objects.create(
        username=f"admin_{company.ruc[-4:]}",
        email=f"admin@{company.email.split('@')[1]}",
        first_name="Carlos",
        last_name="Administrador",
        company=company,
        role='admin',
        position='Gerente General',
        department='Administración',
        is_staff=True,
        is_active=True,
        password=make_password('admin123'),
        email_notifications=True,
        whatsapp_notifications=True
    )
    users.append(admin_user)
    
    # Si es la empresa principal, crear más usuarios
    if is_main:
        # Usuarios operativos detallados
        users_data = [
            ('inventario_mgr', 'María', 'García', 'analyst', 'Jefe de Inventario', 'Logística'),
            ('ventas_sup', 'Roberto', 'Silva', 'analyst', 'Supervisor de Ventas', 'Comercial'),
            ('compras_ana', 'Ana', 'Torres', 'analyst', 'Analista de Compras', 'Logística'),
            ('almacen_jefe', 'Luis', 'Mendoza', 'analyst', 'Jefe de Almacén', 'Operaciones'),
            ('finanzas_cont', 'Carmen', 'Vega', 'analyst', 'Contador', 'Finanzas'),
            ('marketing_eje', 'Diego', 'Flores', 'analyst', 'Ejecutivo Marketing', 'Marketing'),
            ('rrhh_coord', 'Patricia', 'Ruiz', 'analyst', 'Coordinadora RRHH', 'Recursos Humanos'),
            ('ti_sop', 'Miguel', 'Castro', 'analyst', 'Soporte TI', 'Tecnología'),
            ('calidad_esp', 'Elena', 'Morales', 'analyst', 'Especialista Calidad', 'Operaciones'),
            ('logistica_coord', 'Fernando', 'Herrera', 'analyst', 'Coordinador Logística', 'Logística')
        ]
    else:
        # Para empresas demo, menos usuarios
        users_data = [
            ('inventario', 'Supervisor', 'Inventario', 'analyst', 'Supervisor', 'Operaciones'),
            ('ventas', 'Ejecutivo', 'Ventas', 'analyst', 'Ejecutivo', 'Comercial'),
            ('compras', 'Analista', 'Compras', 'analyst', 'Analista', 'Logística')
        ]
    
    for username_suffix, first_name, last_name, role, position, department in users_data:
        user = User.objects.create(
            username=f"{username_suffix}_{company.ruc[-4:]}",
            email=f"{username_suffix}@{company.email.split('@')[1]}",
            first_name=first_name,
            last_name=last_name,
            company=company,
            role=role,
            position=position,
            department=department,
            phone=f"+51-{random.randint(900000000, 999999999)}",
            is_active=True,
            password=make_password('user123'),
            email_notifications=True,
            whatsapp_notifications=random.choice([True, False])
        )
        users.append(user)
    
    print(f"   ✅ {len(users)} usuarios creados")
    return users

def create_categories():
    """Crear categorías de productos realistas del mercado peruano"""
    print("\n📂 CREANDO CATEGORÍAS...")
    
    categories_data = [
        ('Lácteos y Derivados', 'Leches, yogures, quesos y productos lácteos'),
        ('Bebidas', 'Gaseosas, jugos, agua, bebidas energéticas'),
        ('Snacks y Dulces', 'Chocolates, galletas, caramelos, bocaditos'),
        ('Cuidado Personal', 'Shampoo, jabones, pasta dental, desodorantes'),
        ('Panadería y Repostería', 'Panes, tortas, pasteles, productos de panadería'),
        ('Condimentos y Especias', 'Sazonadores, condimentos, especias'),
        ('Conservas y Enlatados', 'Atún, conservas de pescado, vegetales enlatados'),
        ('Cereales y Granos', 'Avena, quinua, cereales para desayuno'),
        ('Limpieza del Hogar', 'Detergentes, desinfectantes, productos de limpieza'),
        ('Carnes y Embutidos', 'Jamones, salchichas, productos cárnicos'),
        ('Abarrotes Básicos', 'Arroz, azúcar, aceite, harina, fideos'),
        ('Frutas y Verduras', 'Productos frescos, frutas y vegetales')
    ]
    
    categories = {}
    for name, description in categories_data:
        category = Category.objects.create(
            name=name,
            description=description,
            is_active=True
        )
        categories[name] = category
        print(f"   ✅ {name}")
    
    return categories

def create_suppliers():
    """Crear proveedores realistas del mercado peruano"""
    print("\n🚚 CREANDO PROVEEDORES...")
    
    suppliers_data = [
        {
            'name': 'Gloria SA',
            'contact_name': 'Carlos Mendoza Rivera',
            'email': 'carlos.mendoza@gloria.com.pe',
            'phone': '+51-1-715-1000',
            'address': 'Av. República de Panamá 2461, La Victoria, Lima',
            'city': 'Lima',
            'tax_id': '20100190797',
            'payment_terms': '30 días'
        },
        {
            'name': 'Nestlé Perú SA',
            'contact_name': 'María García Solís',
            'email': 'maria.garcia@nestle.pe',
            'phone': '+51-1-411-9000',
            'address': 'Av. Santo Toribio 143, San Isidro, Lima',
            'city': 'Lima',
            'tax_id': '20100152425',
            'payment_terms': '45 días'
        },
        {
            'name': 'Unilever Andina Perú SA',
            'contact_name': 'Roberto Silva Morales',
            'email': 'roberto.silva@unilever.pe',
            'phone': '+51-1-200-6000',
            'address': 'Av. Córdova 578, Miraflores, Lima',
            'city': 'Lima',
            'tax_id': '20100130204',
            'payment_terms': '60 días'
        },
        {
            'name': 'Alicorp SAA',
            'contact_name': 'Ana Torres Vega',
            'email': 'ana.torres@alicorp.com.pe',
            'phone': '+51-1-315-0000',
            'address': 'Av. Argentina 4793, Carmen de la Legua, Callao',
            'city': 'Callao',
            'tax_id': '20100055237',
            'payment_terms': '30 días'
        },
        {
            'name': 'Mondelez Perú SA',
            'contact_name': 'Luis Herrera Castro',
            'email': 'luis.herrera@mondelez.pe',
            'phone': '+51-1-610-7000',
            'address': 'Av. Cristóbal de Peralta Norte 820, Santiago de Surco, Lima',
            'city': 'Lima',
            'tax_id': '20509830871',
            'payment_terms': '45 días'
        },
        {
            'name': 'Ajinomoto del Perú SA',
            'contact_name': 'Patricia Ruiz Flores',
            'email': 'patricia.ruiz@ajinomoto.pe',
            'phone': '+51-1-517-3000',
            'address': 'Av. Encalada 1420, Santiago de Surco, Lima',
            'city': 'Lima',
            'tax_id': '20100128056',
            'payment_terms': '45 días'
        }
    ]
    
    suppliers = {}
    for supplier_data in suppliers_data:
        supplier = Supplier.objects.create(**supplier_data)
        suppliers[supplier.name] = supplier
        print(f"   ✅ {supplier.name}")
    
    return suppliers

def create_locations_for_company(company, is_main=False):
    """Crear ubicaciones/almacenes para una empresa específica"""
    print(f"\n📍 CREANDO UBICACIONES PARA {company.name}...")
    
    locations = []
    company_suffix = company.ruc[-3:]  # Usar últimos 3 dígitos del RUC para hacer códigos únicos
    
    if is_main:
        # Empresa principal: más ubicaciones detalladas
        locations_data = [
            ('Almacén Principal Callao', f'APC-{company_suffix}-001', 'Centro de distribución principal', 'A', 'A1', 'R01', 'S01'),
            ('Almacén Lima Centro', f'ALC-{company_suffix}-002', 'Almacén de distribución urbana', 'B', 'B1', 'R02', 'S01'),
            ('Cámara Refrigerada', f'REF-{company_suffix}-003', 'Almacenamiento de productos refrigerados', 'C', 'C1', 'R03', 'S01'),
            ('Almacén Lima Norte', f'ALN-{company_suffix}-004', 'Sucursal Lima Norte', 'D', 'D1', 'R04', 'S01'),
            ('Almacén Lima Sur', f'ALS-{company_suffix}-005', 'Sucursal Lima Sur', 'E', 'E1', 'R05', 'S01'),
            ('Cross Docking', f'CRD-{company_suffix}-006', 'Área de cross docking y tránsito', 'F', 'F1', 'R06', 'S01'),
            ('Almacén Temporal', f'ATM-{company_suffix}-007', 'Almacenamiento temporal de mercadería', 'G', 'G1', 'R07', 'S01')
        ]
    else:
        # Empresas demo: ubicaciones básicas
        locations_data = [
            ('Almacén Principal', f'APR-{company_suffix}-001', 'Almacén principal', 'A', 'A1', 'R01', 'S01'),
            ('Almacén Secundario', f'ASE-{company_suffix}-002', 'Almacén secundario', 'B', 'B1', 'R02', 'S01'),
            ('Área de Tránsito', f'ATR-{company_suffix}-003', 'Área de tránsito', 'C', 'C1', 'R03', 'S01')
        ]
    
    for name, code, description, zone, aisle, rack, shelf in locations_data:
        location = Location.objects.create(
            name=name,
            code=code,
            description=description,
            warehouse=f"Centro de Distribución {company.name}",
            zone=zone,
            aisle=aisle,
            rack=rack,
            shelf=shelf,
            is_active=True
        )
        locations.append(location)
    
    print(f"   ✅ {len(locations)} ubicaciones creadas")
    return locations

def create_products(companies, categories, suppliers):
    """Crear productos realistas para cada empresa"""
    print("\n📦 CREANDO PRODUCTOS...")
    
    # Productos base realistas del mercado peruano
    products_data = [
        # Lácteos y Derivados
        ('Aceite Primor 1L', 'LAC-001', 'Lácteos y Derivados', 'Gloria SA', 8.50, 12.00, 50, 10, 200),
        ('Leche Gloria Entera 1L', 'LAC-002', 'Lácteos y Derivados', 'Gloria SA', 4.20, 5.80, 100, 20, 300),
        ('Yogurt Gloria Fresa 1L', 'LAC-003', 'Lácteos y Derivados', 'Gloria SA', 6.80, 9.50, 30, 5, 150),
        ('Queso Bonlé Edam 250g', 'LAC-004', 'Lácteos y Derivados', 'Gloria SA', 12.50, 17.00, 25, 5, 100),
        ('Leche Gloria Descremada 1L', 'LAC-005', 'Lácteos y Derivados', 'Gloria SA', 4.50, 6.20, 80, 15, 250),
        
        # Bebidas
        ('Coca Cola 2L', 'BEB-001', 'Bebidas', 'Alicorp SAA', 5.50, 8.00, 150, 30, 500),
        ('Sprite 2L', 'BEB-002', 'Bebidas', 'Alicorp SAA', 5.50, 8.00, 120, 25, 400),
        ('Inca Kola 2L', 'BEB-003', 'Bebidas', 'Alicorp SAA', 5.80, 8.50, 100, 20, 350),
        ('Agua San Luis 625ml', 'BEB-004', 'Bebidas', 'Nestlé Perú SA', 1.20, 2.00, 200, 50, 1000),
        ('Nescafé Clásico 170g', 'BEB-005', 'Bebidas', 'Nestlé Perú SA', 8.90, 12.50, 40, 10, 150),
        
        # Snacks y Dulces
        ('Sublime Clásico 30g', 'SNK-001', 'Snacks y Dulces', 'Nestlé Perú SA', 1.80, 2.50, 300, 50, 1000),
        ('Donuts Bimbo x6', 'SNK-002', 'Snacks y Dulces', 'Mondelez Perú SA', 4.20, 6.00, 80, 20, 300),
        ('Galletas Oreo 432g', 'SNK-003', 'Snacks y Dulces', 'Mondelez Perú SA', 8.50, 12.00, 60, 15, 200),
        
        # Cuidado Personal
        ('Shampu Sedal 340ml', 'CUI-001', 'Cuidado Personal', 'Unilever Andina Perú SA', 6.80, 9.50, 40, 10, 150),
        ('Jabón Dove 90g', 'CUI-002', 'Cuidado Personal', 'Unilever Andina Perú SA', 2.80, 4.00, 100, 25, 400),
        ('Pasta Dental Close Up 60ml', 'CUI-003', 'Cuidado Personal', 'Unilever Andina Perú SA', 3.50, 5.00, 80, 20, 300),
        
        # Panadería y Repostería
        ('Pan Bimbo Grande', 'PAN-001', 'Panadería y Repostería', 'Mondelez Perú SA', 3.80, 5.50, 60, 15, 200),
        ('Pan Bimbo Integral', 'PAN-002', 'Panadería y Repostería', 'Mondelez Perú SA', 4.20, 6.00, 50, 12, 180),
        
        # Condimentos y Especias
        ('Maggi Cubito Gallina 8und', 'CON-001', 'Condimentos y Especias', 'Nestlé Perú SA', 2.50, 3.50, 200, 40, 800),
        
        # Cereales y Granos
        ('Cerelac Trigo 400g', 'CER-001', 'Cereales y Granos', 'Nestlé Perú SA', 12.80, 18.00, 30, 8, 120),
        
        # Limpieza del Hogar
        ('Detergente Ariel 780g', 'LIM-001', 'Limpieza del Hogar', 'Unilever Andina Perú SA', 8.90, 12.50, 50, 12, 200),
        
        # Abarrotes Básicos
        ('Fideos Don Vittorio Spaghetti 500g', 'ABA-001', 'Abarrotes Básicos', 'Alicorp SAA', 2.80, 4.00, 150, 30, 600),
        ('Arroz Superior Extra 5kg', 'ABA-002', 'Abarrotes Básicos', 'Alicorp SAA', 18.50, 25.00, 40, 10, 150),
        ('Azúcar Rubia 1kg', 'ABA-003', 'Abarrotes Básicos', 'Alicorp SAA', 3.20, 4.50, 100, 25, 400),
        ('Atún Florida en Aceite 170g', 'ABA-004', 'Conservas y Enlatados', 'Alicorp SAA', 4.80, 6.80, 80, 20, 300),
        ('Harina Blanca Flor 1kg', 'ABA-005', 'Abarrotes Básicos', 'Alicorp SAA', 3.80, 5.20, 70, 18, 280),
        ('Cerveza Pilsen 330ml x6', 'BEB-006', 'Bebidas', 'Alicorp SAA', 15.50, 22.00, 60, 15, 240)
    ]
    
    products = {}
    
    for company_name, company in companies.items():
        company_products = []
        
        for name, sku, category_name, supplier_name, cost, sale, stock, min_stock, max_stock in products_data:
            # Agregar sufijo único por empresa
            unique_sku = f"{sku}-{company.ruc[-3:]}"
            
            # Variación de precios por empresa (+/- 10%)
            cost_variation = random.uniform(0.9, 1.1)
            sale_variation = random.uniform(0.9, 1.1)
            
            product = Product.objects.create(
                name=name,
                sku=unique_sku,
                description=f"{name} - Producto de calidad premium para {company.name}",
                company=company,
                category=categories[category_name],
                supplier=suppliers[supplier_name],
                cost_price=Decimal(str(round(cost * cost_variation, 2))),
                sale_price=Decimal(str(round(sale * sale_variation, 2))),
                stock=stock + random.randint(-10, 20),  # Variación en stock
                min_stock=min_stock,
                max_stock=max_stock,
                reorder_point=min_stock + 5,
                unit='unidad',
                barcode=f"77{random.randint(10000000, 99999999)}{random.randint(10, 99)}",
                weight=Decimal(str(random.uniform(0.1, 2.0))),
                dimensions=f"{random.randint(5, 25)}x{random.randint(5, 25)}x{random.randint(5, 25)}",
                track_batches=category_name in ['Lácteos y Derivados', 'Conservas y Enlatados'],
                has_expiration=category_name in ['Lácteos y Derivados', 'Panadería y Repostería', 'Conservas y Enlatados'],
                shelf_life_days=random.randint(30, 730) if category_name in ['Lácteos y Derivados', 'Conservas y Enlatados'] else None,
                is_active=True
            )
            company_products.append(product)
        
        products[company_name] = company_products
        print(f"   ✅ {len(company_products)} productos para {company.name}")
    
    return products

def create_customers(companies):
    """Crear clientes realistas para cada empresa"""
    print("\n👥 CREANDO CLIENTES...")
    
    customers_base = [
        ('Corporación Wong SA', 'corporacion@wong.pe', '+51-1-611-5000', 'business', '20100070970'),
        ('Plaza Vea SA', 'contacto@plazavea.com.pe', '+51-1-618-2300', 'business', '20100017491'),
        ('Makro Supermayorista SA', 'ventas@makro.pe', '+51-1-500-4300', 'business', '20100152524'),
        ('Cencosud Retail Perú SA', 'info@cencosud.pe', '+51-1-211-3300', 'business', '20109072177'),
        ('Tottus SA', 'contacto@tottus.pe', '+51-1-200-2300', 'business', '20508565934'),
        ('José García López', 'jose.garcia@email.com', '+51-987-654-321', 'individual', '12345678'),
        ('María Rodríguez Pérez', 'maria.rodriguez@email.com', '+51-987-123-456', 'individual', '87654321'),
        ('Carlos Mendoza Silva', 'carlos.mendoza@email.com', '+51-998-765-432', 'individual', '11223344'),
        ('Ana Torres Vega', 'ana.torres@email.com', '+51-976-543-210', 'individual', '55667788'),
        ('Roberto Silva Morales', 'roberto.silva@email.com', '+51-965-432-109', 'individual', '99887766')
    ]
    
    customers = {}
    
    for company_name, company in companies.items():
        company_customers = []
        
        for name, email, phone, customer_type, tax_id in customers_base:
            # Agregar sufijo único por empresa para evitar duplicados
            unique_email = f"{email.split('@')[0]}_{company.ruc[-3:]}@{email.split('@')[1]}"
            
            customer = Customer.objects.create(
                name=name,
                email=unique_email,
                phone=phone,
                address=f"Dirección comercial {name}",
                city='Lima',
                country='Perú',
                tax_id=f"{tax_id}{company.ruc[-2:]}",
                customer_type=customer_type,
                credit_limit=Decimal(str(random.randint(5000, 50000))) if customer_type == 'business' else Decimal('1000'),
                is_active=True
            )
            company_customers.append(customer)
        
        customers[company_name] = company_customers
        print(f"   ✅ {len(company_customers)} clientes para {company.name}")
    
    return customers

def create_leads(companies, products, users):
    """Crear leads/prospectos realistas"""
    print("\n🎯 CREANDO LEADS...")
    
    leads_base = [
        ('Minimarket Los Olivos', 'minimarket.olivos@email.com', '+51-1-234-5678', 'Minimarket Los Olivos EIRL', 'web', 'new'),
        ('Bodega San Juan', 'bodega.sanjuan@email.com', '+51-1-345-6789', 'Bodega San Juan', 'referral', 'contacted'),
        ('Restaurante El Buen Sabor', 'restaurante.sabor@email.com', '+51-1-456-7890', 'El Buen Sabor SAC', 'phone', 'qualified'),
        ('Distribuidora Regional', 'dist.regional@email.com', '+51-1-567-8901', 'Distribuidora Regional SRL', 'email', 'proposal'),
        ('Cadena de Farmacias', 'farmacias.cadena@email.com', '+51-1-678-9012', 'Farmacias Unidos SA', 'social', 'negotiation')
    ]
    
    leads = {}
    
    for company_name, company in companies.items():
        company_leads = []
        company_users = users[company_name]
        company_products = products[company_name]
        
        for name, email, phone, company_str, source, status in leads_base:
            unique_email = f"{email.split('@')[0]}_{company.ruc[-3:]}@{email.split('@')[1]}"
            
            lead = Lead.objects.create(
                name=name,
                email=unique_email,
                phone=phone,
                company=company_str,
                source=source,
                status=status,
                notes=f"Lead potencial para {company.name}. Interesado en productos de calidad.",
                estimated_value=Decimal(str(random.randint(5000, 25000))),
                expected_close_date=timezone.now().date() + timedelta(days=random.randint(15, 90)),
                assigned_to=random.choice(company_users[1:])  # No asignar al admin
            )
            
            # Asignar productos de interés (2-5 productos aleatorios)
            interested_products = random.sample(company_products, random.randint(2, min(5, len(company_products))))
            lead.interested_products.set(interested_products)
            
            company_leads.append(lead)
        
        leads[company_name] = company_leads
        print(f"   ✅ {len(company_leads)} leads para {company.name}")
    
    return leads

def create_realistic_transactions(companies, products, locations, users):
    """Crear transacciones históricas realistas para 18 meses"""
    print("\n💰 CREANDO TRANSACCIONES HISTÓRICAS (18 MESES)...")
    
    # Fecha de inicio: 18 meses atrás
    start_date = timezone.now().date() - timedelta(days=540)
    end_date = timezone.now().date()
    
    total_transactions = 0
    
    for company_name, company in companies.items():
        print(f"\n   🏢 {company.name}:")
        company_products = products[company_name]
        company_locations = locations[company_name]
        company_users = users[company_name]
        
        company_transactions = 0
        
        # Crear transacciones mes por mes para patrones realistas
        current_date = start_date
        
        while current_date <= end_date:
            month_end = min(current_date + timedelta(days=30), end_date)
            
            # Patrones estacionales
            month = current_date.month
            seasonal_multiplier = 1.0
            if month in [12, 1]:  # Navidad y Año Nuevo
                seasonal_multiplier = 1.8
            elif month in [7, 8]:  # Fiestas Patrias y vacaciones
                seasonal_multiplier = 1.4
            elif month in [11]:  # Pre-navidad
                seasonal_multiplier = 1.3
            elif month in [2, 3]:  # Post-fiestas
                seasonal_multiplier = 0.7
            
            month_name = current_date.strftime("%B %Y")
            
            # Transacciones de compras (ingresos)
            purchase_count = int(random.randint(15, 30) * seasonal_multiplier)
            for _ in range(purchase_count):
                product = random.choice(company_products)
                location = random.choice(company_locations)
                user = random.choice(company_users)
                
                # Cantidades realistas de compra
                if 'Aceite' in product.name or 'Arroz' in product.name:
                    quantity = random.randint(50, 200)  # Productos de alto volumen
                elif 'Coca Cola' in product.name or 'Agua' in product.name:
                    quantity = random.randint(100, 500)  # Bebidas
                else:
                    quantity = random.randint(20, 100)  # Productos regulares
                
                # Fecha aleatoria en el mes
                transaction_date = current_date + timedelta(
                    days=random.randint(0, (month_end - current_date).days),
                    hours=random.randint(8, 17),
                    minutes=random.randint(0, 59)
                )
                
                Transaction.objects.create(
                    product=product,
                    location=location,
                    transaction_type='purchase',
                    quantity=Decimal(str(quantity)),
                    unit_cost=product.cost_price * Decimal(str(random.uniform(0.95, 1.05))),  # Variación de precio
                    reference_number=f'COMP-{transaction_date.strftime("%Y%m")}-{random.randint(1000, 9999)}',
                    notes=f'Compra {month_name}',
                    transaction_date=transaction_date,
                    created_by=user
                )
                company_transactions += 1
            
            # Transacciones de ventas (salidas) - CANTIDADES NEGATIVAS
            sales_count = int(random.randint(80, 150) * seasonal_multiplier)
            for _ in range(sales_count):
                product = random.choice(company_products)
                location = random.choice(company_locations)
                user = random.choice(company_users)
                
                # Cantidades realistas de venta (NEGATIVAS)
                if 'Agua' in product.name or 'Coca Cola' in product.name:
                    base_quantity = random.randint(5, 30)  # Bebidas populares
                elif 'Sublime' in product.name or 'Galletas' in product.name:
                    base_quantity = random.randint(10, 50)  # Snacks
                elif 'Leche' in product.name or 'Yogurt' in product.name:
                    base_quantity = random.randint(3, 15)  # Lácteos
                else:
                    base_quantity = random.randint(1, 20)  # Productos regulares
                
                quantity = -int(base_quantity * seasonal_multiplier)  # NEGATIVO para ventas
                
                transaction_date = current_date + timedelta(
                    days=random.randint(0, (month_end - current_date).days),
                    hours=random.randint(9, 19),  # Horario comercial extendido
                    minutes=random.randint(0, 59)
                )
                
                Transaction.objects.create(
                    product=product,
                    location=location,
                    transaction_type='sale',
                    quantity=Decimal(str(quantity)),
                    unit_cost=product.sale_price,  # Precio de venta
                    reference_number=f'VENT-{transaction_date.strftime("%Y%m")}-{random.randint(1000, 9999)}',
                    notes=f'Venta {month_name}',
                    transaction_date=transaction_date,
                    created_by=user
                )
                company_transactions += 1
            
            # Ajustes de inventario ocasionales
            if random.random() < 0.3:  # 30% de probabilidad por mes
                adjustment_count = random.randint(1, 5)
                for _ in range(adjustment_count):
                    product = random.choice(company_products)
                    location = random.choice(company_locations)
                    user = random.choice(company_users)
                    
                    # Ajustes pueden ser positivos o negativos
                    quantity = random.randint(-10, 15)
                    
                    transaction_date = current_date + timedelta(
                        days=random.randint(0, (month_end - current_date).days),
                        hours=random.randint(8, 17),
                        minutes=random.randint(0, 59)
                    )
                    
                    Transaction.objects.create(
                        product=product,
                        location=location,
                        transaction_type='adjustment',
                        quantity=Decimal(str(quantity)),
                        unit_cost=product.cost_price if quantity > 0 else None,
                        reference_number=f'AJU-{transaction_date.strftime("%Y%m")}-{random.randint(1000, 9999)}',
                        notes=f'Ajuste inventario {month_name}',
                        transaction_date=transaction_date,
                        created_by=user
                    )
                    company_transactions += 1
            
            print(f"      📅 {month_name}: {int((purchase_count + sales_count) * seasonal_multiplier)} transacciones")
            current_date = month_end + timedelta(days=1)
        
        total_transactions += company_transactions
        print(f"   ✅ Total: {company_transactions} transacciones")
    
    print(f"\n🎉 TOTAL TRANSACCIONES CREADAS: {total_transactions}")
    return total_transactions

def create_inventory_items(products, locations):
    """Crear items de inventario basados en transacciones"""
    print("\n📦 CREANDO ITEMS DE INVENTARIO...")
    
    inventory_count = 0
    
    for company_name, company_products in products.items():
        company_locations = locations[company_name]
        
        for product in company_products:
            for location in company_locations:
                # Calcular stock real basado en transacciones
                total_transactions = Transaction.objects.filter(
                    product=product,
                    location=location
                )
                
                total_quantity = sum(float(t.quantity) for t in total_transactions)
                final_stock = max(0, total_quantity)  # No puede ser negativo
                
                if final_stock > 0:
                    # Calcular costo promedio ponderado
                    purchase_transactions = total_transactions.filter(
                        transaction_type='purchase',
                        unit_cost__isnull=False
                    )
                    
                    if purchase_transactions.exists():
                        total_cost = sum(float(t.quantity) * float(t.unit_cost) for t in purchase_transactions)
                        total_purchase_qty = sum(float(t.quantity) for t in purchase_transactions)
                        avg_cost = total_cost / total_purchase_qty if total_purchase_qty > 0 else float(product.cost_price)
                    else:
                        avg_cost = float(product.cost_price)
                    
                    InventoryItem.objects.create(
                        product=product,
                        location=location,
                        quantity=Decimal(str(round(final_stock, 2))),
                        reserved_quantity=Decimal(str(round(final_stock * random.uniform(0, 0.1), 2))),  # 0-10% reservado
                        unit_cost=Decimal(str(round(avg_cost, 4))),
                        batch_number=f'LOTE-{product.sku[-3:]}-{location.code[-2:]}-{random.randint(100, 999)}',
                        manufacturing_date=timezone.now().date() - timedelta(days=random.randint(30, 180)),
                        expiration_date=timezone.now().date() + timedelta(days=random.randint(180, 730)) if product.has_expiration else None,
                        is_active=True
                    )
                    inventory_count += 1
    
    print(f"✅ Items de inventario creados: {inventory_count}")
    return inventory_count

def create_sales_records(products, customers, users):
    """Crear registros de ventas históricas"""
    print("\n💵 CREANDO REGISTROS DE VENTAS...")
    
    sales_count = 0
    
    for company_name, company_products in products.items():
        company_customers = customers[company_name]
        company_users = users[company_name]
        
        # Crear 200-500 ventas históricas por empresa
        num_sales = random.randint(200, 500)
        
        for _ in range(num_sales):
            product = random.choice(company_products)
            customer = random.choice(company_customers)
            
            quantity = random.randint(1, 20)
            unit_price = product.sale_price * Decimal(str(random.uniform(0.95, 1.05)))  # Variación de precio
            
            # Fecha aleatoria en los últimos 12 meses
            sale_date = timezone.now() - timedelta(days=random.randint(1, 365))
            
            Sale.objects.create(
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                customer_name=customer.name,
                date_sold=sale_date
            )
            sales_count += 1
    
    print(f"✅ Registros de ventas creados: {sales_count}")
    return sales_count

def create_alerts(products):
    """Crear alertas realistas del sistema"""
    print("\n🚨 CREANDO ALERTAS...")
    
    alerts_count = 0
    
    for company_name, company_products in products.items():
        for product in company_products:
            # Calcular stock actual basado en InventoryItems
            current_stock = sum(
                float(item.quantity) for item in 
                InventoryItem.objects.filter(product=product)
            )
            
            # Alertas de stock bajo
            if current_stock <= product.min_stock:
                severity = 'high' if current_stock < product.min_stock * 0.5 else 'medium'
                Alert.objects.create(
                    product=product,
                    message=f'Stock bajo para {product.name}. Stock actual: {current_stock:.1f}, mínimo: {product.min_stock}',
                    severity=severity,
                    is_active=True
                )
                alerts_count += 1
            
            # Alertas de productos próximos a vencer
            if product.has_expiration:
                inventory_items = InventoryItem.objects.filter(
                    product=product,
                    expiration_date__isnull=False
                )
                
                for item in inventory_items:
                    days_to_expire = (item.expiration_date - timezone.now().date()).days
                    if 0 < days_to_expire <= 30:
                        severity = 'high' if days_to_expire <= 7 else 'medium'
                        Alert.objects.create(
                            product=product,
                            message=f'Producto {product.name} en {item.location.name} vence en {days_to_expire} días',
                            severity=severity,
                            is_active=True
                        )
                        alerts_count += 1
    
    print(f"✅ Alertas creadas: {alerts_count}")
    return alerts_count

def create_inventory_history(products, users):
    """Crear historial de cambios de inventario"""
    print("\n📈 CREANDO HISTORIAL DE INVENTARIO...")
    
    history_count = 0
    
    for company_name, company_products in products.items():
        company_users = users[company_name]
        
        # Crear 5-15 registros de historial por producto
        for product in company_products[:10]:  # Solo primeros 10 productos para no sobrecargar
            num_records = random.randint(5, 15)
            
            for i in range(num_records):
                old_stock = random.randint(50, 200)
                change = random.randint(-30, 50)
                new_stock = max(0, old_stock + change)
                
                reasons = [
                    'Venta realizada',
                    'Compra recibida',
                    'Ajuste de inventario',
                    'Transferencia entre ubicaciones',
                    'Devolución de cliente',
                    'Merma identificada',
                    'Conteo físico'
                ]
                
                InventoryHistory.objects.create(
                    product=product,
                    stock_before=old_stock,
                    stock_after=new_stock,
                    change_reason=random.choice(reasons),
                    user=random.choice(company_users),
                    date_changed=timezone.now() - timedelta(days=random.randint(1, 180))
                )
                history_count += 1
    
    print(f"✅ Registros de historial creados: {history_count}")
    return history_count

def main():
    """Función principal para crear todos los datos - SOLO UNA EMPRESA"""
    print("🚀 INICIANDO CREACIÓN DE DATOS PARA UNA SOLA EMPRESA")
    print("=" * 60)
    
    # Paso 1: Limpiar datos existentes
    clear_existing_data()
    
    # Paso 2: Crear solo la empresa principal
    main_company = create_main_company()
    
    # Solo una empresa
    companies = {main_company.name: main_company}
    
    # Solo usuarios para la empresa principal
    users = {}
    users[main_company.name] = create_users_for_company(main_company, is_main=True)
    
    # Datos base (compartidos)
    categories = create_categories()
    suppliers = create_suppliers()
    
    # Solo ubicaciones para la empresa principal
    locations = {}
    locations[main_company.name] = create_locations_for_company(main_company, is_main=True)
    
    # Paso 3: Crear productos y relaciones para la empresa principal
    products = create_products(companies, categories, suppliers)
    customers = create_customers(companies)
    leads = create_leads(companies, products, users)
    
    # Paso 4: Crear datos transaccionales
    create_realistic_transactions(companies, products, locations, users)
    create_inventory_items(products, locations)
    create_sales_records(products, customers, users)
    
    # Paso 5: Crear datos operativos
    create_alerts(products)
    create_inventory_history(products, users)
    
    print("\n" + "=" * 60)
    print("🎉 CREACIÓN DE DATOS COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    
    # Resumen final
    print("\n📊 RESUMEN FINAL:")
    print(f"   🏢 Empresa: {Company.objects.count()}")
    print(f"   👥 Usuarios: {User.objects.filter(is_superuser=False).count()}")
    print(f"   📂 Categorías: {Category.objects.count()}")
    print(f"   🚚 Proveedores: {Supplier.objects.count()}")
    print(f"   📍 Ubicaciones: {Location.objects.count()}")
    print(f"   📦 Productos: {Product.objects.count()}")
    print(f"   👤 Clientes: {Customer.objects.count()}")
    print(f"   🎯 Leads: {Lead.objects.count()}")
    print(f"   💰 Transacciones: {Transaction.objects.count()}")
    print(f"   📦 Items inventario: {InventoryItem.objects.count()}")
    print(f"   💵 Ventas: {Sale.objects.count()}")
    print(f"   🚨 Alertas: {Alert.objects.count()}")
    print(f"   📈 Historial: {InventoryHistory.objects.count()}")
    
    print("\n✅ Sistema listo para usar con datos realistas!")
    print("🔑 Credenciales de acceso:")
    print("   📧 Usuario: admin_6789")
    print("   🔐 Contraseña: admin123")
    print("   🏢 Empresa: Distribuidora San Martín SAC")
    print("   💼 Email: admin@sanmartin.com.pe")

if __name__ == '__main__':
    main()