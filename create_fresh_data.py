#!/usr/bin/env python
"""
Script para crear datos de prueba con la nueva estructura
"""
import os
import sys
import django
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
    InventoryItem, Transaction, Sale, Alert
)

User = get_user_model()

def create_fresh_data():
    """Crear datos de prueba frescos para la nueva estructura"""
    print("🚀 Creando datos de prueba con la nueva estructura...")
    
    # 1. Crear empresa principal
    company, created = Company.objects.get_or_create(
        name='Distribuidora San Martín SAC',
        defaults={
            'ruc': '20123456789',
            'address': 'Av. San Martín 123, Lima, Perú',
            'phone': '+51 1 234-5678',
            'email': 'contacto@sanmartin.com.pe',
            'industry': 'Distribución',
            'is_active': True
        }
    )
    print(f"✅ Empresa: {company.name}")
    
    # 2. Crear categorías
    categories_data = [
        {'name': 'Abarrotes', 'description': 'Productos de primera necesidad'},
        {'name': 'Bebidas', 'description': 'Gaseosas, jugos y agua'},
        {'name': 'Lácteos', 'description': 'Leche, quesos y yogures'},
        {'name': 'Panadería', 'description': 'Pan y productos de panadería'},
        {'name': 'Limpieza', 'description': 'Productos de limpieza del hogar'},
        {'name': 'Cuidado Personal', 'description': 'Productos de higiene personal'},
        {'name': 'Snacks', 'description': 'Galletas, dulces y bocaditos'},
        {'name': 'Congelados', 'description': 'Productos congelados'}
    ]
    
    categories = {}
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        categories[cat_data['name']] = category
    print(f"✅ Categorías creadas: {len(categories)}")
    
    # 3. Crear proveedores
    suppliers_data = [
        {
            'name': 'Gloria S.A.',
            'contact_name': 'Carlos Mendoza',
            'email': 'ventas@gloria.com.pe',
            'phone': '+51 1 345-6789',
            'city': 'Lima',
            'tax_id': '20100190797'
        },
        {
            'name': 'Alicorp S.A.A.',
            'contact_name': 'María González',
            'email': 'comercial@alicorp.com.pe',
            'phone': '+51 1 456-7890',
            'city': 'Lima',
            'tax_id': '20100055237'
        },
        {
            'name': 'Coca Cola Perú',
            'contact_name': 'Luis Ramírez',
            'email': 'ventas@cocacola.com.pe',
            'phone': '+51 1 567-8901',
            'city': 'Lima',
            'tax_id': '20100113610'
        },
        {
            'name': 'Nestlé Perú S.A.',
            'contact_name': 'Ana Torres',
            'email': 'ventas@nestle.com.pe',
            'phone': '+51 1 678-9012',
            'city': 'Lima',
            'tax_id': '20100166594'
        },
        {
            'name': 'Bimbo Perú',
            'contact_name': 'Pedro Silva',
            'email': 'ventas@bimbo.com.pe',
            'phone': '+51 1 789-0123',
            'city': 'Lima',
            'tax_id': '20100123456'
        }
    ]
    
    suppliers = {}
    for sup_data in suppliers_data:
        supplier, created = Supplier.objects.get_or_create(
            name=sup_data['name'],
            defaults=sup_data
        )
        suppliers[sup_data['name']] = supplier
    print(f"✅ Proveedores creados: {len(suppliers)}")
    
    # 4. Crear ubicaciones
    locations_data = [
        {
            'name': 'Almacén Principal',
            'code': 'ALM-01',
            'warehouse': 'Lima Centro',
            'zone': 'A',
            'aisle': '01'
        },
        {
            'name': 'Almacén Secundario',
            'code': 'ALM-02',
            'warehouse': 'Lima Norte',
            'zone': 'B',
            'aisle': '02'
        },
        {
            'name': 'Refrigerado',
            'code': 'REF-01',
            'warehouse': 'Lima Centro',
            'zone': 'C',
            'aisle': '03'
        }
    ]
    
    locations = {}
    for loc_data in locations_data:
        location, created = Location.objects.get_or_create(
            code=loc_data['code'],
            defaults=loc_data
        )
        locations[loc_data['name']] = location
    print(f"✅ Ubicaciones creadas: {len(locations)}")
    
    # 5. Crear productos peruanos realistas
    products_data = [
        {
            'name': 'Leche Gloria Entera 1L',
            'sku': 'LAC-001',
            'category': 'Lácteos',
            'supplier': 'Gloria S.A.',
            'cost_price': Decimal('3.20'),
            'sale_price': Decimal('4.50'),
            'stock': 120,
            'min_stock': 20,
            'max_stock': 200
        },
        {
            'name': 'Aceite Primor 1L',
            'sku': 'ABA-001',
            'category': 'Abarrotes',
            'supplier': 'Alicorp S.A.A.',
            'cost_price': Decimal('8.50'),
            'sale_price': Decimal('12.00'),
            'stock': 80,
            'min_stock': 15,
            'max_stock': 150
        },
        {
            'name': 'Coca Cola 2L',
            'sku': 'BEB-001',
            'category': 'Bebidas',
            'supplier': 'Coca Cola Perú',
            'cost_price': Decimal('4.80'),
            'sale_price': Decimal('7.00'),
            'stock': 150,
            'min_stock': 30,
            'max_stock': 250
        },
        {
            'name': 'Maggi Cubito 8und',
            'sku': 'ABA-002',
            'category': 'Abarrotes',
            'supplier': 'Nestlé Perú S.A.',
            'cost_price': Decimal('2.10'),
            'sale_price': Decimal('3.50'),
            'stock': 200,
            'min_stock': 50,
            'max_stock': 300
        },
        {
            'name': 'Yogurt Gloria Fresa 1L',
            'sku': 'LAC-002',
            'category': 'Lácteos',
            'supplier': 'Gloria S.A.',
            'cost_price': Decimal('5.20'),
            'sale_price': Decimal('7.50'),
            'stock': 45,
            'min_stock': 10,
            'max_stock': 100
        },
        {
            'name': 'Pan Bimbo Integral',
            'sku': 'PAN-001',
            'category': 'Panadería',
            'supplier': 'Bimbo Perú',
            'cost_price': Decimal('3.80'),
            'sale_price': Decimal('5.50'),
            'stock': 65,
            'min_stock': 20,
            'max_stock': 120
        },
        {
            'name': 'Fideos Don Vittorio 500g',
            'sku': 'ABA-003',
            'category': 'Abarrotes',
            'supplier': 'Alicorp S.A.A.',
            'cost_price': Decimal('2.80'),
            'sale_price': Decimal('4.20'),
            'stock': 180,
            'min_stock': 40,
            'max_stock': 250
        },
        {
            'name': 'Agua San Luis 625ml',
            'sku': 'BEB-002',
            'category': 'Bebidas',
            'supplier': 'Nestlé Perú S.A.',
            'cost_price': Decimal('1.20'),
            'sale_price': Decimal('2.00'),
            'stock': 300,
            'min_stock': 100,
            'max_stock': 500
        },
        {
            'name': 'Detergente Ariel 780g',
            'sku': 'LIM-001',
            'category': 'Limpieza',
            'supplier': 'Alicorp S.A.A.',
            'cost_price': Decimal('12.50'),
            'sale_price': Decimal('18.90'),
            'stock': 60,
            'min_stock': 15,
            'max_stock': 120
        },
        {
            'name': 'Galletas Oreo 432g',
            'sku': 'SNK-001',
            'category': 'Snacks',
            'supplier': 'Nestlé Perú S.A.',
            'cost_price': Decimal('6.80'),
            'sale_price': Decimal('9.50'),
            'stock': 90,
            'min_stock': 25,
            'max_stock': 150
        }
    ]
    
    products = {}
    for prod_data in products_data:
        product_data = prod_data.copy()
        product_data['category'] = categories[prod_data['category']]
        product_data['supplier'] = suppliers[prod_data['supplier']]
        product_data['company'] = company
        product_data['price'] = prod_data['sale_price']
        product_data['unit'] = 'unidad'
        
        product, created = Product.objects.get_or_create(
            sku=prod_data['sku'],
            defaults=product_data
        )
        products[prod_data['name']] = product
    print(f"✅ Productos creados: {len(products)}")
    
    # 6. Crear clientes
    customers_data = [
        {
            'name': 'Bodega San Pedro',
            'email': 'pedidos@bodegasanpedro.com',
            'phone': '+51 1 789-0123',
            'address': 'Jr. San Pedro 456, Lima',
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
            'name': 'Juan Carlos Pérez',
            'email': 'jcperez@email.com',
            'phone': '+51 987 654 321',
            'address': 'Calle Los Olivos 123, Miraflores',
            'city': 'Lima',
            'tax_id': '12345678',
            'customer_type': 'individual',
            'credit_limit': Decimal('1000.00')
        }
    ]
    
    customers = {}
    for cust_data in customers_data:
        customer, created = Customer.objects.get_or_create(
            tax_id=cust_data['tax_id'],
            defaults=cust_data
        )
        customers[cust_data['name']] = customer
    print(f"✅ Clientes creados: {len(customers)}")
    
    # 7. Crear leads
    user = User.objects.first()
    leads_data = [
        {
            'name': 'María Gonzales',
            'email': 'maria.gonzales@email.com',
            'phone': '+51 987 123 456',
            'company': 'Bodega Central',
            'source': 'web',
            'status': 'new',
            'estimated_value': Decimal('3000.00'),
            'notes': 'Interesada en productos lácteos',
            'assigned_to': user
        },
        {
            'name': 'Carlos Rodriguez',
            'email': 'carlos.rodriguez@minimarket.com',
            'phone': '+51 976 543 210',
            'company': 'Minimarket Rodriguez',
            'source': 'referral',
            'status': 'qualified',
            'estimated_value': Decimal('5000.00'),
            'notes': 'Busca proveedor de bebidas',
            'assigned_to': user
        }
    ]
    
    leads = {}
    for lead_data in leads_data:
        lead, created = Lead.objects.get_or_create(
            email=lead_data['email'],
            defaults=lead_data
        )
        leads[lead_data['name']] = lead
    print(f"✅ Leads creados: {len(leads)}")
    
    # 8. Crear algunas ventas
    sales_count = 0
    for i, (product_name, product) in enumerate(list(products.items())[:5]):
        customer = list(customers.values())[i % len(customers)]
        
        Sale.objects.get_or_create(
            product=product,
            customer_name=customer.name,
            defaults={
                'quantity': 5 + (i % 10),
                'unit_price': product.sale_price,
                'date_sold': timezone.now() - timedelta(days=i*2)
            }
        )
        sales_count += 1
    print(f"✅ Ventas creadas: {sales_count}")
    
    # 9. Crear alertas para productos con stock bajo
    alerts_count = 0
    for product in products.values():
        if product.stock <= product.min_stock:
            Alert.objects.get_or_create(
                product=product,
                defaults={
                    'message': f'Stock bajo para {product.name}. Stock actual: {product.stock}, mínimo: {product.min_stock}',
                    'severity': 'high' if product.stock < product.min_stock * 0.5 else 'medium'
                }
            )
            alerts_count += 1
    print(f"✅ Alertas creadas: {alerts_count}")
    
    print("\n🎉 ¡Datos de prueba creados exitosamente con la nueva estructura!")
    print(f"📊 Resumen:")
    print(f"   - Empresa: {company.name}")
    print(f"   - Categorías: {len(categories)}")
    print(f"   - Proveedores: {len(suppliers)}")
    print(f"   - Productos: {len(products)}")
    print(f"   - Ubicaciones: {len(locations)}")
    print(f"   - Clientes: {len(customers)}")
    print(f"   - Leads: {len(leads)}")
    print(f"   - Ventas: {sales_count}")
    print(f"   - Alertas: {alerts_count}")
    print(f"\n🔑 Credenciales de acceso:")
    print(f"   - Email: superadmin@datalens.com")
    print(f"   - Password: admin123")

if __name__ == '__main__':
    create_fresh_data()