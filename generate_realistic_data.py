#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script completo para generar datos realistas de DataLens
Incluye: Inventario, CRM, Usuarios, Empresas, Transacciones, y más
Ejecutar con: python generate_realistic_data.py
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
import random
from faker import Faker

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from authentication.models import Company, User
from inventory.models import (
    Category, Supplier, Location, Product, InventoryItem, Transaction,
    Customer, Lead, Opportunity, OpportunityProduct, Contact, Activity,
    CustomFieldDefinition, CustomFieldValue
)

# Configurar Faker en español
fake = Faker('es_ES')  # Faker para España (más compatible)
Faker.seed(12345)  # Para resultados consistentes

# Datos realistas peruanos
COMPANY_NAMES = [
    "Distribuidora San Martín SAC", "Comercial Los Andes EIRL", "Importadora Lima Norte SAC",
    "Grupo Empresarial Cusco SA", "Inversiones Arequipa SAC", "Corporación Trujillo EIRL",
    "Negocios Chiclayo SAC", "Comercializadora Iquitos SA", "Distribuidora Huancayo EIRL"
]

PRODUCT_CATEGORIES = {
    "Alimentos y Bebidas": {
        "subcategories": ["Granos Andinos", "Condimentos", "Conservas", "Bebidas", "Lácteos", "Carnes"],
        "products": [
            {"name": "Quinua Real Premium", "base_price": 15.50},
            {"name": "Kiwicha Orgánica", "base_price": 12.80},
            {"name": "Ají Amarillo en Pasta", "base_price": 8.50},
            {"name": "Café Orgánico Villa Rica", "base_price": 28.00},
            {"name": "Maca Gelatinizada", "base_price": 45.00},
            {"name": "Camu Camu en Polvo", "base_price": 120.00}
        ]
    },
    "Textiles y Confecciones": {
        "subcategories": ["Alpaca", "Algodón Pima", "Textiles Tradicionales", "Accesorios"],
        "products": [
            {"name": "Poncho de Alpaca Baby", "base_price": 180.00},
            {"name": "Camiseta Pima Cotton", "base_price": 35.00},
            {"name": "Bufanda Alpaca Natural", "base_price": 65.00},
            {"name": "Chalina Vicuña", "base_price": 450.00}
        ]
    },
    "Artesanías": {
        "subcategories": ["Cerámica", "Textiles Artesanales", "Joyería", "Decoración"],
        "products": [
            {"name": "Vasija Shipibo Tradicional", "base_price": 85.00},
            {"name": "Tapiz Ayacuchano", "base_price": 220.00},
            {"name": "Collar de Plata Huanca", "base_price": 150.00},
            {"name": "Retablo Ayacuchano", "base_price": 320.00}
        ]
    },
    "Productos Naturales": {
        "subcategories": ["Superalimentos", "Hierbas Medicinales", "Cosméticos Naturales"],
        "products": [
            {"name": "Sacha Inchi Tostado", "base_price": 25.00},
            {"name": "Lúcuma en Polvo", "base_price": 22.00},
            {"name": "Aceite de Coco Virgen", "base_price": 18.50},
            {"name": "Uña de Gato Extracto", "base_price": 55.00}
        ]
    }
}

SUPPLIER_DATA = [
    {"name": "Agroexportadora Andes SAC", "city": "Lima", "industry": "Agricultura"},
    {"name": "Textiles Alpaca del Sur EIRL", "city": "Cusco", "industry": "Textiles"},
    {"name": "Artesanías Perú Export SAC", "city": "Ayacucho", "industry": "Artesanías"},
    {"name": "Cooperativa Café Norte", "city": "Jaén", "industry": "Agricultura"},
    {"name": "Superfoods Amazonas SAC", "city": "Iquitos", "industry": "Alimentos"},
    {"name": "Manufacturas Lima SAC", "city": "Lima", "industry": "Manufactura"}
]

CUSTOMER_COMPANIES = [
    "Restaurante Central", "Hotel Belmond", "Supermercados Plaza Vea",
    "Restaurant Astrid y Gastón", "Hotel Country Club", "Tottus Supermercados",
    "Whole Foods Market", "Trader Joe's", "Williams Sonoma",
    "Anthropologie", "Free People", "Nordstrom"
]

LEAD_SOURCES = ["website", "social_media", "email_marketing", "referral", "cold_call", "event", "advertisement"]
OPPORTUNITY_STAGES = ["prospecting", "qualification", "needs_analysis", "value_proposition", "proposal", "negotiation"]


def create_companies():
    """Crear empresas realistas"""
    companies = []
    
    for i, company_name in enumerate(COMPANY_NAMES[:3]):  # Crear 3 empresas
        ruc = f"201234567{i:02d}"
        company_data = {
            'name': company_name,
            'ruc': ruc,
            'address': fake.address(),
            'phone': fake.phone_number(),
            'email': fake.email(),
            'industry': random.choice(['Comercio', 'Distribución', 'Importación', 'Exportación']),
            'website': f"https://www.{company_name.lower().replace(' ', '').replace('sac', '').replace('eirl', '').replace('sa', '')}.com.pe",
            'subscription_type': random.choice(['basic', 'premium', 'enterprise']),
            'max_users': random.choice([10, 50, 100, 500])
        }
        
        company, created = Company.objects.get_or_create(
            ruc=ruc,
            defaults=company_data
        )
        companies.append(company)
        print(f"{'✓ Creada' if created else '→ Encontrada'} empresa: {company.name}")
    
    return companies


def create_users(companies):
    """Crear usuarios realistas para cada empresa"""
    users = []
    roles = ['admin', 'manager', 'employee', 'viewer']
    
    for company in companies:
        # Crear 5-8 usuarios por empresa
        num_users = random.randint(5, 8)
        
        for i in range(num_users):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}.{last_name.lower()}"
            
            user_data = {
                'username': username,
                'email': f"{username}@{company.name.lower().replace(' ', '').replace('sac', '').replace('eirl', '')}.com.pe",
                'first_name': first_name,
                'last_name': last_name,
                'role': roles[0] if i == 0 else random.choice(roles[1:]),
                'is_active': True,
                'company': company
            }
            
            user, created = User.objects.get_or_create(
                username=username,
                company=company,
                defaults=user_data
            )
            
            if created:
                user.set_password('password123')  # Contraseña temporal
                user.save()
            
            users.append(user)
            print(f"  {'✓ Creado' if created else '→ Encontrado'} usuario: {user.get_full_name()} ({user.role})")
    
    return users


def create_categories_and_products(company):
    """Crear categorías y productos realistas"""
    categories = {}
    products = {}
    
    for main_cat, cat_data in PRODUCT_CATEGORIES.items():
        # Crear categoría principal
        main_category, created = Category.objects.get_or_create(
            company=company,
            name=main_cat,
            defaults={'description': f'Categoría de {main_cat.lower()}'}
        )
        categories[main_cat] = main_category
        
        # Crear subcategorías
        for subcat_name in cat_data['subcategories']:
            subcategory, created = Category.objects.get_or_create(
                company=company,
                name=subcat_name,
                parent=main_category,
                defaults={'description': f'Subcategoría de {subcat_name}'}
            )
            categories[subcat_name] = subcategory
        
        # Crear productos para esta categoría
        for product_info in cat_data['products']:
            sku = f"{main_cat[:3].upper()}-{fake.random_int(min=1000, max=9999)}"
            cost_price = Decimal(str(product_info['base_price']))
            sale_price = cost_price * Decimal('1.5')  # 50% markup
            
            product_data = {
                'company': company,
                'sku': sku,
                'name': product_info['name'],
                'description': fake.text(max_nb_chars=200),
                'category': subcategory,
                'unit': random.choice(['kg', 'unit', 'liter', 'box', 'pack']),
                'cost_price': cost_price,
                'sale_price': sale_price,
                'min_stock': random.randint(10, 50),
                'max_stock': random.randint(100, 500),
                'reorder_point': random.randint(20, 80),
                'weight': Decimal(str(random.uniform(0.1, 5.0))),
                'barcode': fake.ean13(),
                'track_batches': random.choice([True, False]),
                'has_expiration': random.choice([True, False]),
                'shelf_life_days': random.randint(180, 1095) if random.choice([True, False]) else None
            }
            
            product, created = Product.objects.get_or_create(
                company=company,
                sku=sku,
                defaults=product_data
            )
            products[sku] = product
            print(f"  {'✓ Creado' if created else '→ Encontrado'} producto: {product.name}")
    
    return categories, products


def create_suppliers_and_locations(company):
    """Crear proveedores y ubicaciones realistas"""
    suppliers = {}
    locations = {}
    
    # Crear proveedores
    for supplier_info in SUPPLIER_DATA:
        ruc = f"20{fake.random_int(min=100000000, max=999999999)}"
        
        supplier_data = {
            'company': company,
            'name': supplier_info['name'],
            'ruc': ruc,
            'contact_person': fake.name(),
            'email': fake.email(),
            'phone': fake.phone_number(),
            'address': fake.address(),
            'payment_terms': random.choice(['15 días', '30 días', '45 días', '60 días']),
            'credit_limit': Decimal(str(random.randint(10000, 200000))),
            'lead_time': random.randint(3, 30)
        }
        
        supplier, created = Supplier.objects.get_or_create(
            company=company,
            ruc=ruc,
            defaults=supplier_data
        )
        suppliers[supplier_info['name']] = supplier
        print(f"  {'✓ Creado' if created else '→ Encontrado'} proveedor: {supplier.name}")
    
    # Crear ubicaciones de almacén
    location_types = [
        "Recepción", "Almacén Principal", "Cámara Fría", "Productos Secos",
        "Textiles", "Artesanías", "Expedición", "Cuarentena"
    ]
    
    for i, location_name in enumerate(location_types):
        location_data = {
            'company': company,
            'name': location_name,
            'code': f"LOC-{i+1:03d}",
            'description': f"Ubicación para {location_name.lower()}",
            'warehouse': "Almacén Central",
            'zone': chr(65 + i),  # A, B, C, etc.
            'aisle': f"{i+1:02d}",
            'rack': "01",
            'shelf': "01"
        }
        
        location, created = Location.objects.get_or_create(
            company=company,
            code=location_data['code'],
            defaults=location_data
        )
        locations[location_name] = location
        print(f"  {'✓ Creada' if created else '→ Encontrada'} ubicación: {location.name}")
    
    return suppliers, locations


def create_inventory_and_transactions(company, products, suppliers, locations, users):
    """Crear inventario inicial y transacciones"""
    admin_user = users[0]  # Usar el primer usuario como admin
    
    # Asignar proveedores aleatorios a productos
    supplier_list = list(suppliers.values())
    location_list = list(locations.values())
    
    for product in products.values():
        if not product.supplier:
            product.supplier = random.choice(supplier_list)
            product.save()
    
    # Crear inventario inicial
    for product in products.values():
        location = random.choice(location_list)
        
        # Cantidad inicial entre min y max stock
        initial_qty = Decimal(str(random.uniform(
            float(product.min_stock), 
            float(product.max_stock)
        )))
        
        inventory_data = {
            'product': product,
            'location': location,
            'quantity': initial_qty,
            'reserved_quantity': Decimal('0.00'),
            'unit_cost': product.cost_price
        }
        
        # Agregar datos de lote si corresponde
        if product.track_batches:
            batch_date = fake.date_between(start_date='-6M', end_date='today')
            inventory_data['batch_number'] = f"LT{batch_date.strftime('%Y%m%d')}{random.randint(1, 99):02d}"
            inventory_data['manufacturing_date'] = batch_date
            
            if product.has_expiration and product.shelf_life_days:
                expiration_date = batch_date + timedelta(days=product.shelf_life_days)
                inventory_data['expiration_date'] = expiration_date
        
        inventory_item, created = InventoryItem.objects.get_or_create(
            product=product,
            location=location,
            defaults=inventory_data
        )
        
        # Crear transacción de inventario inicial
        if created:
            transaction_data = {
                'company': company,
                'transaction_type': 'initial',
                'reference_number': f"INI-{fake.random_int(min=1000, max=9999)}",
                'product': product,
                'location': location,
                'quantity': initial_qty,
                'unit_cost': product.cost_price,
                'user': admin_user,
                'transaction_date': fake.date_time_between(start_date='-3M', end_date='now'),
                'notes': f'Inventario inicial - {product.name}'
            }
            
            Transaction.objects.create(**transaction_data)
    
    # Crear transacciones adicionales
    transaction_types = ['purchase', 'sale', 'adjustment', 'transfer']
    
    for _ in range(50):  # 50 transacciones adicionales
        product = random.choice(list(products.values()))
        location = random.choice(location_list)
        trans_type = random.choice(transaction_types)
        
        # Determinar cantidad según tipo
        if trans_type == 'sale':
            quantity = -Decimal(str(random.uniform(1, 50)))
        else:
            quantity = Decimal(str(random.uniform(1, 100)))
        
        transaction_data = {
            'company': company,
            'transaction_type': trans_type,
            'reference_number': f"{trans_type.upper()[:3]}-{fake.random_int(min=1000, max=9999)}",
            'product': product,
            'location': location,
            'quantity': quantity,
            'unit_cost': product.cost_price,
            'user': random.choice(users),
            'transaction_date': fake.date_time_between(start_date='-2M', end_date='now'),
            'notes': fake.sentence()
        }
        
        Transaction.objects.create(**transaction_data)


def create_crm_data(company, users):
    """Crear datos completos de CRM"""
    print("\n=== Creando datos CRM ===")
    
    # Crear clientes
    customers = []
    for _ in range(25):  # 25 clientes
        customer_type = random.choice(['individual', 'business'])
        
        if customer_type == 'business':
            business_name = random.choice(CUSTOMER_COMPANIES)
            customer_data = {
                'company': company,
                'customer_type': 'business',
                'business_name': business_name,
                'trade_name': business_name,
                'document_type': 'RUC',
                'document_number': f"20{fake.random_int(min=100000000, max=999999999)}",
                'email': fake.email(),
                'phone': fake.phone_number(),
                'address': fake.address(),
                'city': fake.city(),
                'industry': random.choice(['Restaurantes', 'Hoteles', 'Retail', 'Exportación']),
                'annual_revenue': Decimal(str(random.randint(100000, 5000000))),
                'assigned_to': random.choice(users),
                'status': random.choice(['active', 'inactive', 'prospect']),
                'acquisition_source': random.choice(['Website', 'Referencia', 'Evento', 'Publicidad'])
            }
        else:
            customer_data = {
                'company': company,
                'customer_type': 'individual',
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'document_type': 'DNI',
                'document_number': fake.random_int(min=10000000, max=99999999),
                'email': fake.email(),
                'phone': fake.phone_number(),
                'address': fake.address(),
                'city': fake.city(),
                'assigned_to': random.choice(users),
                'status': random.choice(['active', 'inactive', 'prospect']),
                'acquisition_source': random.choice(['Website', 'Referencia', 'Redes Sociales'])
            }
        
        customer = Customer.objects.create(**customer_data)
        customers.append(customer)
        print(f"  ✓ Cliente: {customer.display_name}")
    
    # Crear leads
    leads = []
    for _ in range(40):  # 40 leads
        lead_data = {
            'company': company,
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'phone': fake.phone_number(),
            'company_name': fake.company(),
            'job_title': fake.job(),
            'status': random.choice(['new', 'contacted', 'qualified', 'proposal']),
            'source': random.choice(LEAD_SOURCES),
            'score': random.randint(0, 100),
            'industry': random.choice(['Retail', 'Restaurantes', 'Exportación', 'Manufactura']),
            'budget': Decimal(str(random.randint(5000, 500000))),
            'assigned_to': random.choice(users),
            'notes': fake.text(max_nb_chars=200)
        }
        
        lead = Lead.objects.create(**lead_data)
        leads.append(lead)
        print(f"  ✓ Lead: {lead.first_name} {lead.last_name} - {lead.company_name}")
    
    # Crear oportunidades
    opportunities = []
    for _ in range(30):  # 30 oportunidades
        customer = random.choice(customers) if random.choice([True, False]) else None
        lead = random.choice(leads) if not customer and random.choice([True, False]) else None
        
        opportunity_data = {
            'company': company,
            'name': f"Oportunidad {fake.catch_phrase()}",
            'description': fake.text(max_nb_chars=300),
            'customer': customer,
            'lead': lead,
            'stage': random.choice(OPPORTUNITY_STAGES),
            'probability': random.randint(10, 90),
            'amount': Decimal(str(random.randint(10000, 1000000))),
            'currency': 'PEN',
            'expected_close_date': fake.date_between(start_date='today', end_date='+6M'),
            'assigned_to': random.choice(users)
        }
        
        opportunity = Opportunity.objects.create(**opportunity_data)
        opportunities.append(opportunity)
        print(f"  ✓ Oportunidad: {opportunity.name} - S/ {opportunity.amount}")
    
    # Crear contactos
    for customer in customers[:15]:  # Contactos para algunos clientes
        for _ in range(random.randint(1, 3)):  # 1-3 contactos por cliente
            contact_data = {
                'company': company,
                'customer': customer,
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'job_title': fake.job(),
                'contact_type': random.choice(['primary', 'secondary', 'technical', 'billing']),
                'email': fake.email(),
                'phone': fake.phone_number(),
                'department': random.choice(['Ventas', 'Compras', 'Finanzas', 'Operaciones']),
                'notes': fake.sentence()
            }
            
            contact = Contact.objects.create(**contact_data)
            print(f"    ✓ Contacto: {contact.full_name} ({contact.job_title})")
    
    # Crear actividades
    activity_types = ['call', 'email', 'meeting', 'task', 'demo', 'follow_up']
    
    for _ in range(100):  # 100 actividades
        customer = random.choice(customers) if random.choice([True, False]) else None
        lead = random.choice(leads) if not customer and random.choice([True, False]) else None
        opportunity = random.choice(opportunities) if random.choice([True, False]) else None
        
        activity_data = {
            'company': company,
            'title': f"{fake.catch_phrase()} - {random.choice(activity_types).title()}",
            'description': fake.text(max_nb_chars=200),
            'activity_type': random.choice(activity_types),
            'status': random.choice(['planned', 'completed', 'cancelled']),
            'customer': customer,
            'lead': lead,
            'opportunity': opportunity,
            'scheduled_date': fake.date_time_between(start_date='-1M', end_date='+1M'),
            'assigned_to': random.choice(users),
            'outcome': fake.sentence() if random.choice([True, False]) else '',
            'duration_minutes': random.randint(15, 120)
        }
        
        activity = Activity.objects.create(**activity_data)
        print(f"    ✓ Actividad: {activity.title}")
    
    return customers, leads, opportunities


def create_custom_fields(company):
    """Crear campos personalizados de ejemplo"""
    print("\n=== Creando campos personalizados ===")
    
    custom_fields_data = [
        {
            'model_type': 'product',
            'field_name': 'certificacion_organica',
            'field_label': 'Certificación Orgánica',
            'field_type': 'boolean',
            'is_required': False,
            'help_text': 'Indica si el producto tiene certificación orgánica'
        },
        {
            'model_type': 'product',
            'field_name': 'pais_origen',
            'field_label': 'País de Origen',
            'field_type': 'choice',
            'choices_json': '[{"value": "PE", "label": "Perú"}, {"value": "BO", "label": "Bolivia"}, {"value": "EC", "label": "Ecuador"}]',
            'is_required': True
        },
        {
            'model_type': 'customer',
            'field_name': 'nivel_descuento',
            'field_label': 'Nivel de Descuento',
            'field_type': 'choice',
            'choices_json': '[{"value": "bronze", "label": "Bronze (5%)"}, {"value": "silver", "label": "Silver (10%)"}, {"value": "gold", "label": "Gold (15%)"}]'
        },
        {
            'model_type': 'customer',
            'field_name': 'fecha_ultimo_pedido',
            'field_label': 'Fecha Último Pedido',
            'field_type': 'date',
            'help_text': 'Fecha del último pedido realizado'
        }
    ]
    
    for field_data in custom_fields_data:
        field_data['company'] = company
        custom_field = CustomFieldDefinition.objects.create(**field_data)
        print(f"  ✓ Campo personalizado: {custom_field.field_label} ({custom_field.model_type})")


def main():
    """Función principal"""
    print("🚀 === GENERANDO DATOS REALISTAS PARA DATALENS === 🚀\n")
    
    try:
        # 1. Crear empresas
        print("1️⃣ Creando empresas...")
        companies = create_companies()
        main_company = companies[0]  # Usar la primera empresa como principal
        
        # 2. Crear usuarios
        print("\n2️⃣ Creando usuarios...")
        users = create_users([main_company])
        
        # 3. Crear categorías y productos
        print("\n3️⃣ Creando categorías y productos...")
        categories, products = create_categories_and_products(main_company)
        
        # 4. Crear proveedores y ubicaciones
        print("\n4️⃣ Creando proveedores y ubicaciones...")
        suppliers, locations = create_suppliers_and_locations(main_company)
        
        # 5. Crear inventario y transacciones
        print("\n5️⃣ Creando inventario y transacciones...")
        create_inventory_and_transactions(main_company, products, suppliers, locations, users)
        
        # 6. Crear datos CRM
        print("\n6️⃣ Creando datos CRM...")
        customers, leads, opportunities = create_crm_data(main_company, users)
        
        # 7. Crear campos personalizados
        print("\n7️⃣ Creando campos personalizados...")
        create_custom_fields(main_company)
        
        # Resumen final
        print("\n" + "="*60)
        print("🎉 ¡DATOS GENERADOS EXITOSAMENTE! 🎉")
        print("="*60)
        print(f"🏢 Empresa principal: {main_company.name}")
        print(f"👥 Usuarios: {len(users)}")
        print(f"📦 Productos: {len(products)}")
        print(f"🏪 Proveedores: {len(suppliers)}")
        print(f"📍 Ubicaciones: {len(locations)}")
        print(f"👤 Clientes: {len(customers)}")
        print(f"🎯 Leads: {len(leads)}")
        print(f"💼 Oportunidades: {len(opportunities)}")
        
        # Calcular valor total del inventario
        total_inventory_value = sum(
            item.quantity * item.unit_cost 
            for item in InventoryItem.objects.filter(product__company=main_company)
        )
        print(f"💰 Valor total inventario: S/ {total_inventory_value:,.2f}")
        
        # Calcular valor total del pipeline CRM
        total_pipeline_value = sum(
            opp.amount for opp in opportunities 
            if opp.stage not in ['closed_won', 'closed_lost']
        )
        print(f"📈 Valor total pipeline: S/ {total_pipeline_value:,.2f}")
        
        print("\n✅ El sistema está listo para usar con datos realistas!")
        print("📊 Puedes acceder al admin en: http://localhost:8080/admin/")
        print("🔗 API disponible en: http://localhost:8080/api/")
        
    except Exception as e:
        print(f"❌ Error al generar datos: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)