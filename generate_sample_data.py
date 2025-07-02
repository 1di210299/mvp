#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para generar datos de prueba con productos peruanos tipicos
Ejecutar con: python manage.py shell < generate_sample_data.py
O: python generate_sample_data.py (si se configura DJANGO_SETTINGS_MODULE)
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from authentication.models import Company, User
from inventory.models import Category, Supplier, Location, Product, InventoryItem, Transaction


def create_sample_company():
    """Crear una empresa de ejemplo"""
    company, created = Company.objects.get_or_create(
        ruc='20123456789',
        defaults={
            'name': 'Distribuidora Lima SAC',
            'address': 'Av. La Marina 2355, San Miguel, Lima',
            'phone': '01-4567890',
            'email': 'contacto@distribuidoralima.com',
            'industry': 'Distribucion y Comercio',
            'website': 'https://distribuidoralima.com',
            'subscription_type': 'premium',
        }
    )
    print(f"{'Creada' if created else 'Encontrada'} empresa: {company.name}")
    return company
            'website': 'https://distribuidoralima.com',
            'subscription_type': 'premium',
        }
    )
    print(f"{'Creada' if created else 'Encontrada'} empresa: {company.name}")
    return company


def create_categories(company):
    """Crear categorias de productos peruanos"""
    categories_data = [
        {
            'name': 'Alimentos y Bebidas',
            'description': 'Productos alimenticios y bebidas',
            'subcategories': [
                'Granos y Cereales',
                'Condimentos y Especias',
                'Conservas',
                'Bebidas',
                'Lacteos',
                'Carnes y Embutidos'
            ]
        },
        {
            'name': 'Textiles',
            'description': 'Productos textiles y prendas de vestir',
            'subcategories': [
                'Algodón Pima',
                'Alpaca',
                'Prendas Tradicionales',
                'Accesorios'
            ]
        },
        {
            'name': 'Artesanias',
            'description': 'Productos artesanales peruanos',
            'subcategories': [
                'Ceramica',
                'Textiles Artesanales',
                'Joyeria',
                'Decoracion'
            ]
        },
        {
            'name': 'Productos Naturales',
            'description': 'Productos naturales y medicinales',
            'subcategories': [
                'Hierbas Medicinales',
                'Superalimentos',
                'Cosméticos Naturales'
            ]
        }
    ]
    
    categories = {}
    for cat_data in categories_data:
        # Crear categoría principal
        category, created = Category.objects.get_or_create(
            company=company,
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        categories[cat_data['name']] = category
        print(f"{'Creada' if created else 'Encontrada'} categoría: {category.name}")
        
        # Crear subcategorías
        for subcat_name in cat_data['subcategories']:
            subcategory, created = Category.objects.get_or_create(
                company=company,
                name=subcat_name,
                defaults={
                    'description': f'Subcategoría de {cat_data["name"]}',
                    'parent': category
                }
            )
            categories[subcat_name] = subcategory
            print(f"  {'Creada' if created else 'Encontrada'} subcategoria: {subcategory.name}")
    
    return categories


def create_suppliers(company):
    """Crear proveedores peruanos"""
    suppliers_data = [
        {
            'name': 'Agroexportadora Los Andes SAC',
            'ruc': '20587456123',
            'contact_person': 'Carlos Mendoza',
            'email': 'cmendoza@losandes.com.pe',
            'phone': '01-2345678',
            'address': 'Calle Las Flores 123, La Molina, Lima',
            'payment_terms': '30 dias',
            'credit_limit': 50000,
            'lead_time': 7
        },
        {
            'name': 'Textiles Cusco EIRL',
            'ruc': '20456789012',
            'contact_person': 'María Quispe',
            'email': 'mquispe@textilescusco.com.pe',
            'phone': '084-234567',
            'address': 'Av. El Sol 456, Cusco',
            'payment_terms': '45 dias',
            'credit_limit': 75000,
            'lead_time': 14
        },
        {
            'name': 'Cooperativa Agraria Café del Norte',
            'ruc': '20345678901',
            'contact_person': 'José Rodríguez',
            'email': 'jrodriguez@cafenorte.coop',
            'phone': '076-345678',
            'address': 'Jr. Comercio 789, Jaen, Cajamarca',
            'payment_terms': '60 dias',
            'credit_limit': 30000,
            'lead_time': 10
        },
        {
            'name': 'Artesanías Shipibo SAC',
            'ruc': '20234567890',
            'contact_person': 'Ana Vásquez',
            'email': 'avasquez@shipibo.com.pe',
            'phone': '061-456789',
            'address': 'Calle Pucallpa 234, Pucallpa, Ucayali',
            'payment_terms': '30 dias',
            'credit_limit': 20000,
            'lead_time': 21
        },
        {
            'name': 'Superfoods Perú Export SAC',
            'ruc': '20123456780',
            'contact_person': 'Roberto Silva',
            'email': 'rsilva@superfoodspe.com',
            'phone': '01-9876543',
            'address': 'Av. Javier Prado 567, San Isidro, Lima',
            'payment_terms': '15 dias',
            'credit_limit': 100000,
            'lead_time': 5
        }
    ]
    
    suppliers = {}
    for supplier_data in suppliers_data:
        supplier, created = Supplier.objects.get_or_create(
            company=company,
            ruc=supplier_data['ruc'],
            defaults=supplier_data
        )
        suppliers[supplier_data['name']] = supplier
        print(f"{'Creado' if created else 'Encontrado'} proveedor: {supplier.name}")
    
    return suppliers


def create_locations(company):
    """Crear ubicaciones de almacen"""
    locations_data = [
        {
            'name': 'Recepcion',
            'code': 'REC-001',
            'description': 'Area de recepcion de mercancias',
            'warehouse': 'Almacén Principal',
            'zone': 'A',
            'aisle': '01',
            'rack': '01',
            'shelf': '01'
        },
        {
            'name': 'Alimentos Secos',
            'code': 'AS-001',
            'description': 'Zona para productos alimenticios secos',
            'warehouse': 'Almacén Principal',
            'zone': 'B',
            'aisle': '01',
            'rack': '01',
            'shelf': '01'
        },
        {
            'name': 'Refrigerados',
            'code': 'REF-001',
            'description': 'Camara frigorifica',
            'warehouse': 'Almacén Principal',
            'zone': 'C',
            'aisle': '01',
            'rack': '01',
            'shelf': '01'
        },
        {
            'name': 'Textiles',
            'code': 'TEX-001',
            'description': 'Zona para productos textiles',
            'warehouse': 'Almacén Principal',
            'zone': 'D',
            'aisle': '01',
            'rack': '01',
            'shelf': '01'
        },
        {
            'name': 'Artesanias',
            'code': 'ART-001',
            'description': 'Zona para productos artesanales',
            'warehouse': 'Almacén Principal',
            'zone': 'E',
            'aisle': '01',
            'rack': '01',
            'shelf': '01'
        },
        {
            'name': 'Expedicion',
            'code': 'EXP-001',
            'description': 'Area de despacho',
            'warehouse': 'Almacén Principal',
            'zone': 'F',
            'aisle': '01',
            'rack': '01',
            'shelf': '01'
        }
    ]
    
    locations = {}
    for location_data in locations_data:
        location, created = Location.objects.get_or_create(
            company=company,
            code=location_data['code'],
            defaults=location_data
        )
        locations[location_data['name']] = location
        print(f"{'Creada' if created else 'Encontrada'} ubicación: {location.name}")
    
    return locations


def create_products(company, categories, suppliers):
    """Crear productos peruanos tipicos"""
    products_data = [
        # Granos y Cereales
        {
            'sku': 'QUI-001',
            'name': 'Quinua Real Blanca',
            'description': 'Quinua blanca organica del altiplano boliviano-peruano',
            'category': 'Granos y Cereales',
            'supplier': 'Agroexportadora Los Andes SAC',
            'unit': 'kg',
            'cost_price': 12.50,
            'sale_price': 18.75,
            'min_stock': 100,
            'max_stock': 1000,
            'reorder_point': 200,
            'weight': 1.0,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 720
        },
        {
            'sku': 'QUI-002',
            'name': 'Quinua Roja',
            'description': 'Quinua roja premium de los Andes peruanos',
            'category': 'Granos y Cereales',
            'supplier': 'Agroexportadora Los Andes SAC',
            'unit': 'kg',
            'cost_price': 14.00,
            'sale_price': 21.00,
            'min_stock': 50,
            'max_stock': 500,
            'reorder_point': 100,
            'weight': 1.0,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 720
        },
        {
            'sku': 'KIW-001',
            'name': 'Kiwicha (Amaranto)',
            'description': 'Amaranto peruano, super alimento ancestral',
            'category': 'Granos y Cereales',
            'supplier': 'Superfoods Perú Export SAC',
            'unit': 'kg',
            'cost_price': 8.50,
            'sale_price': 12.75,
            'min_stock': 75,
            'max_stock': 750,
            'reorder_point': 150,
            'weight': 1.0,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 540
        },
        # Condimentos y Especias
        {
            'sku': 'AJI-001',
            'name': 'Ají Amarillo en Pasta',
            'description': 'Pasta de ají amarillo peruano, ingrediente esencial',
            'category': 'Condimentos y Especias',
            'supplier': 'Agroexportadora Los Andes SAC',
            'unit': 'kg',
            'cost_price': 6.50,
            'sale_price': 9.75,
            'min_stock': 50,
            'max_stock': 300,
            'reorder_point': 75,
            'weight': 1.0,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 365
        },
        {
            'sku': 'AJI-002',
            'name': 'Ají Panca Molido',
            'description': 'Ají panca deshidratado y molido',
            'category': 'Condimentos y Especias',
            'supplier': 'Agroexportadora Los Andes SAC',
            'unit': 'kg',
            'cost_price': 15.00,
            'sale_price': 22.50,
            'min_stock': 25,
            'max_stock': 200,
            'reorder_point': 50,
            'weight': 1.0,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 720
        },
        # Superalimentos
        {
            'sku': 'MAC-001',
            'name': 'Maca Gelatinizada en Polvo',
            'description': 'Maca peruana gelatinizada de Junín',
            'category': 'Superalimentos',
            'supplier': 'Superfoods Perú Export SAC',
            'unit': 'kg',
            'cost_price': 35.00,
            'sale_price': 52.50,
            'min_stock': 20,
            'max_stock': 150,
            'reorder_point': 40,
            'weight': 1.0,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 1095
        },
        {
            'sku': 'CAM-001',
            'name': 'Camu Camu en Polvo',
            'description': 'Polvo de camu camu amazonico, rico en vitamina C',
            'category': 'Superalimentos',
            'supplier': 'Superfoods Perú Export SAC',
            'unit': 'kg',
            'cost_price': 120.00,
            'sale_price': 180.00,
            'min_stock': 10,
            'max_stock': 50,
            'reorder_point': 15,
            'weight': 1.0,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 730
        },
        {
            'sku': 'LUC-001',
            'name': 'Lúcuma en Polvo',
            'description': 'Polvo de lúcuma deshidratada, endulzante natural',
            'category': 'Superalimentos',
            'supplier': 'Superfoods Perú Export SAC',
            'unit': 'kg',
            'cost_price': 18.00,
            'sale_price': 27.00,
            'min_stock': 30,
            'max_stock': 200,
            'reorder_point': 60,
            'weight': 1.0,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 545
        },
        # Café
        {
            'sku': 'CAF-001',
            'name': 'Café Orgánico de Altura',
            'description': 'Cafe arabica organico de Cajamarca',
            'category': 'Bebidas',
            'supplier': 'Cooperativa Agraria Café del Norte',
            'unit': 'kg',
            'cost_price': 22.00,
            'sale_price': 33.00,
            'min_stock': 100,
            'max_stock': 500,
            'reorder_point': 150,
            'weight': 1.0,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 730
        },
        # Textiles
        {
            'sku': 'ALP-001',
            'name': 'Poncho de Alpaca',
            'description': 'Poncho tradicional de fibra de alpaca 100%',
            'category': 'Alpaca',
            'supplier': 'Textiles Cusco EIRL',
            'unit': 'unit',
            'cost_price': 150.00,
            'sale_price': 225.00,
            'min_stock': 5,
            'max_stock': 25,
            'reorder_point': 8,
            'weight': 0.8,
            'track_batches': False,
            'has_expiration': False
        },
        {
            'sku': 'ALP-002',
            'name': 'Bufanda de Alpaca',
            'description': 'Bufanda suave de fibra de alpaca baby',
            'category': 'Alpaca',
            'supplier': 'Textiles Cusco EIRL',
            'unit': 'unit',
            'cost_price': 45.00,
            'sale_price': 67.50,
            'min_stock': 10,
            'max_stock': 50,
            'reorder_point': 15,
            'weight': 0.2,
            'track_batches': False,
            'has_expiration': False
        },
        {
            'sku': 'ALG-001',
            'name': 'Camiseta Pima Cotton',
            'description': 'Camiseta de algodón Pima peruano premium',
            'category': 'Algodón Pima',
            'supplier': 'Textiles Cusco EIRL',
            'unit': 'unit',
            'cost_price': 25.00,
            'sale_price': 37.50,
            'min_stock': 20,
            'max_stock': 100,
            'reorder_point': 30,
            'weight': 0.2,
            'track_batches': False,
            'has_expiration': False
        },
        # Artesanías
        {
            'sku': 'CER-001',
            'name': 'Vasija de Cerámica Shipibo',
            'description': 'Vasija artesanal con diseños shipibo-konibo',
            'category': 'Cerámica',
            'supplier': 'Artesanías Shipibo SAC',
            'unit': 'unit',
            'cost_price': 35.00,
            'sale_price': 52.50,
            'min_stock': 5,
            'max_stock': 20,
            'reorder_point': 8,
            'weight': 0.5,
            'track_batches': False,
            'has_expiration': False
        },
        {
            'sku': 'TEX-001',
            'name': 'Tapiz Ayacuchano',
            'description': 'Tapiz tejido a mano con motivos ayacuchanos',
            'category': 'Textiles Artesanales',
            'supplier': 'Artesanías Shipibo SAC',
            'unit': 'unit',
            'cost_price': 120.00,
            'sale_price': 180.00,
            'min_stock': 2,
            'max_stock': 10,
            'reorder_point': 4,
            'weight': 1.2,
            'track_batches': False,
            'has_expiration': False
        },
        # Conservas
        {
            'sku': 'ESP-001',
            'name': 'Espárragos en Conserva',
            'description': 'Esparragos blancos peruanos en conserva',
            'category': 'Conservas',
            'supplier': 'Agroexportadora Los Andes SAC',
            'unit': 'unit',
            'cost_price': 4.50,
            'sale_price': 6.75,
            'min_stock': 100,
            'max_stock': 500,
            'reorder_point': 150,
            'weight': 0.4,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 1095
        },
        {
            'sku': 'ACE-001',
            'name': 'Aceitunas Botija',
            'description': 'Aceitunas negras tipo botija de Tacna',
            'category': 'Conservas',
            'supplier': 'Agroexportadora Los Andes SAC',
            'unit': 'kg',
            'cost_price': 8.00,
            'sale_price': 12.00,
            'min_stock': 50,
            'max_stock': 300,
            'reorder_point': 75,
            'weight': 1.0,
            'track_batches': True,
            'has_expiration': True,
            'shelf_life_days': 730
        }
    ]
    
    products = {}
    for product_data in products_data:
        # Obtener la categoría y proveedor
        category = categories.get(product_data['category'])
        supplier = suppliers.get(product_data['supplier'])
        
        # Remover campos que no son del modelo
        model_data = product_data.copy()
        model_data.pop('category')
        model_data.pop('supplier')
        
        # Agregar relaciones
        model_data['category'] = category
        model_data['supplier'] = supplier
        model_data['company'] = company
        
        # Generar codigo de barras simulado
        model_data['barcode'] = f"775{random.randint(100000000, 999999999)}"
        
        product, created = Product.objects.get_or_create(
            company=company,
            sku=product_data['sku'],
            defaults=model_data
        )
        products[product_data['sku']] = product
        print(f"{'Creado' if created else 'Encontrado'} producto: {product.name}")
    
    return products


def create_inventory_items(products, locations):
    """Crear items de inventario con stock inicial"""
    
    # Mapeo de productos a ubicaciones preferidas
    product_locations = {
        'QUI-001': 'Alimentos Secos',
        'QUI-002': 'Alimentos Secos',
        'KIW-001': 'Alimentos Secos',
        'AJI-001': 'Alimentos Secos',
        'AJI-002': 'Alimentos Secos',
        'MAC-001': 'Alimentos Secos',
        'CAM-001': 'Alimentos Secos',
        'LUC-001': 'Alimentos Secos',
        'CAF-001': 'Alimentos Secos',
        'ALP-001': 'Textiles',
        'ALP-002': 'Textiles',
        'ALG-001': 'Textiles',
        'CER-001': 'Artesanías',
        'TEX-001': 'Artesanías',
        'ESP-001': 'Alimentos Secos',
        'ACE-001': 'Refrigerados'
    }
    
    inventory_items = []
    for sku, product in products.items():
        location_name = product_locations.get(sku, 'Alimentos Secos')
        location = locations[location_name]
        
        # Generar cantidad inicial aleatoria entre min_stock y max_stock
        min_qty = float(product.min_stock)
        max_qty = float(product.max_stock)
        # Asegurar que la cantidad inicial sea positiva y esté en el rango correcto
        if min_qty <= 0:
            min_qty = 10  # Valor mínimo por defecto
        if max_qty <= min_qty:
            max_qty = min_qty + 100  # Asegurar que max sea mayor que min
        
        initial_qty = random.uniform(min_qty + 10, max_qty - 10)
        
        # Datos del item de inventario
        inventory_data = {
            'product': product,
            'location': location,
            'quantity': Decimal(str(round(initial_qty, 2))),
            'reserved_quantity': Decimal('0.00'),
            'unit_cost': product.cost_price  # Usar el costo del producto
        }
        
        # Si el producto maneja lotes
        if product.track_batches:
            # Generar numero de lote
            batch_date = datetime.now() - timedelta(days=random.randint(30, 180))
            inventory_data['batch_number'] = f"LT{batch_date.strftime('%Y%m%d')}{random.randint(1, 99):02d}"
            inventory_data['manufacturing_date'] = batch_date.date()
            
            # Si tiene vencimiento
            if product.has_expiration and product.shelf_life_days:
                expiration_date = batch_date + timedelta(days=product.shelf_life_days)
                inventory_data['expiration_date'] = expiration_date.date()
        
        inventory_item, created = InventoryItem.objects.get_or_create(
            product=product,
            location=location,
            defaults=inventory_data
        )
        
        if not created:
            # Si ya existe, actualizar la cantidad
            inventory_item.quantity = inventory_data['quantity']
            inventory_item.save()
        
        inventory_items.append(inventory_item)
        print(f"{'Creado' if created else 'Actualizado'} inventario: {product.name} - {inventory_item.quantity} {product.unit}")
    
    return inventory_items


def create_sample_transactions(company, products, locations):
    """Crear transacciones de ejemplo"""
    
    # Crear un usuario administrador para las transacciones
    admin_user, created = User.objects.get_or_create(
        company=company,
        username='admin',
        defaults={
            'email': 'admin@distribuidoralima.com',
            'first_name': 'Admin',
            'last_name': 'Sistema',
            'role': 'admin'
        }
    )
    
    transactions_data = [
        {
            'product': products['QUI-001'],
            'location': locations['Alimentos Secos'],
            'transaction_type': 'initial',
            'quantity': 500,
            'unit_cost': products['QUI-001'].cost_price,
            'reference_number': 'INI-001',
            'notes': 'Inventario inicial de quinua blanca'
        },
        {
            'product': products['MAC-001'],
            'location': locations['Alimentos Secos'],
            'transaction_type': 'purchase',
            'quantity': 50,
            'unit_cost': products['MAC-001'].cost_price,
            'reference_number': 'PUR-001',
            'notes': 'Compra de maca gelatinizada'
        },
        {
            'product': products['ALP-001'],
            'location': locations['Textiles'],
            'transaction_type': 'purchase',
            'quantity': 10,
            'unit_cost': products['ALP-001'].cost_price,
            'reference_number': 'PUR-002',
            'notes': 'Compra de ponchos de alpaca'
        },
        {
            'product': products['CAF-001'],
            'location': locations['Alimentos Secos'],
            'transaction_type': 'sale',
            'quantity': -25,
            'unit_cost': products['CAF-001'].cost_price,
            'reference_number': 'VEN-001',
            'notes': 'Venta de cafe organico'
        },
        {
            'product': products['CER-001'],
            'location': locations['Artesanias'],
            'transaction_type': 'adjustment',
            'quantity': 2,
            'unit_cost': products['CER-001'].cost_price,
            'reference_number': 'AJU-001',
            'notes': 'Ajuste de inventario - ceramica encontrada'
        }
    ]
    
    transactions = []
    for trans_data in transactions_data:
        # Agregar campos requeridos
        trans_data['company'] = company
        trans_data['created_by'] = admin_user
        
        transaction, created = Transaction.objects.get_or_create(
            company=company,
            reference_number=trans_data['reference_number'],
            defaults=trans_data
        )
        transactions.append(transaction)
        print(f"{'Creada' if created else 'Encontrada'} transaccion: {transaction.reference_number} - {transaction.product.name}")
    
    return transactions


def main():
    """Funcion principal para generar todos los datos"""
    print("=== Generando datos de prueba con productos peruanos ===\n")
    
    try:
        # 1. Crear empresa
        print("1. Creando empresa...")
        company = create_sample_company()
        print()
        
        # 2. Crear categorías
        print("2. Creando categorías...")
        categories = create_categories(company)
        print()
        
        # 3. Crear proveedores
        print("3. Creando proveedores...")
        suppliers = create_suppliers(company)
        print()
        
        # 4. Crear ubicaciones
        print("4. Creando ubicaciones...")
        locations = create_locations(company)
        print()
        
        # 5. Crear productos
        print("5. Creando productos...")
        products = create_products(company, categories, suppliers)
        print()
        
        # 6. Crear inventario inicial
        print("6. Creando inventario inicial...")
        inventory_items = create_inventory_items(products, locations)
        print()
        
        # 7. Crear transacciones de ejemplo
        print("7. Creando transacciones de ejemplo...")
        transactions = create_sample_transactions(company, products, locations)
        print()
        
        print("=== Datos generados exitosamente! ===")
        print(f"- Empresa: {company.name}")
        print(f"- Categorias: {len(categories)}")
        print(f"- Proveedores: {len(suppliers)}")
        print(f"- Ubicaciones: {len(locations)}")
        print(f"- Productos: {len(products)}")
        print(f"- Items de inventario: {len(inventory_items)}")
        
        # Mostrar resumen de stock
        print("\n=== Resumen de Stock ===")
        total_value = Decimal('0.00')
        for product in products.values():
            stock = product.current_stock
            if stock > 0:
                value = Decimal(str(stock)) * product.cost_price
                total_value += value
                print(f"{product.sku} - {product.name}: {stock} {product.unit} (S/ {value:.2f})")
        
        print(f"\nValor total del inventario: S/ {total_value:.2f}")
        
    except Exception as e:
        print(f"Error al generar datos: {e}")
        raise


if __name__ == "__main__":
    main()
