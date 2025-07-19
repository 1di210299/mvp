#!/usr/bin/env python3
"""
Script para crear datos de prueba mínimos para el sistema ML
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal

from authentication.models import Company
from inventory.models import Product, Sale, Customer, Category

def create_test_data():
    """Crear datos de prueba mínimos"""
    print("🏗️ Creando datos de prueba para ML...")
    
    # Obtener o crear company
    company, created = Company.objects.get_or_create(
        name='ML Test Company',
        defaults={
            'description': 'Company for ML testing',
            'email': 'test@mlcompany.com'
        }
    )
    
    if created:
        print(f"✅ Creada nueva company: {company.name}")
    else:
        print(f"✅ Usando company existente: {company.name}")
    
    # Crear categoría
    category, created = Category.objects.get_or_create(
        name='Test Category',
        company=company,
        defaults={'description': 'Test category for ML'}
    )
    
    # Crear productos de prueba
    products = []
    product_names = ['Laptop Pro', 'Mouse Wireless', 'Keyboard Mech', 'Monitor 4K', 'Headphones']
    
    for name in product_names:
        product, created = Product.objects.get_or_create(
            name=name,
            company=company,
            defaults={
                'category': category,
                'price': Decimal(str(np.random.uniform(100, 1000))),
                'stock_level': np.random.randint(50, 200),
                'description': f'Test product {name}'
            }
        )
        products.append(product)
        if created:
            print(f"   ✅ Producto creado: {product.name}")
    
    # Crear clientes
    customers = []
    for i in range(20):
        customer, created = Customer.objects.get_or_create(
            email=f'customer{i}@test.com',
            company=company,
            defaults={
                'name': f'Customer {i}',
                'phone': f'123-456-{i:04d}'
            }
        )
        customers.append(customer)
        if created:
            print(f"   ✅ Cliente creado: {customer.name}")
    
    # Crear ventas históricas (últimos 6 meses)
    start_date = datetime.now() - timedelta(days=180)
    sales_created = 0
    
    for day in range(180):
        current_date = start_date + timedelta(days=day)
        
        # Crear 1-5 ventas por día con patrones estacionales
        daily_sales = np.random.randint(1, 6)
        
        # Agregar patrón semanal (más ventas en fin de semana)
        if current_date.weekday() >= 5:  # Sábado y domingo
            daily_sales = int(daily_sales * 1.5)
        
        for _ in range(daily_sales):
            product = np.random.choice(products)
            customer = np.random.choice(customers)
            
            # Cantidad con distribución realista
            quantity = max(1, int(np.random.exponential(2)))
            
            # Precio con variación
            base_price = float(product.price)
            price_variation = np.random.uniform(0.9, 1.1)
            unit_price = Decimal(str(base_price * price_variation))
            
            sale, created = Sale.objects.get_or_create(
                product=product,
                customer=customer,
                sale_date=current_date.date(),
                quantity=quantity,
                unit_price=unit_price,
                defaults={
                    'total_amount': unit_price * quantity
                }
            )
            
            if created:
                sales_created += 1
    
    print(f"   ✅ Ventas creadas: {sales_created}")
    
    # Verificar datos finales
    total_products = Product.objects.filter(company=company).count()
    total_customers = Customer.objects.filter(company=company).count()
    total_sales = Sale.objects.filter(product__company=company).count()
    
    print(f"\n📊 RESUMEN DE DATOS CREADOS:")
    print(f"   - Company: {company.name}")
    print(f"   - Productos: {total_products}")
    print(f"   - Clientes: {total_customers}")
    print(f"   - Ventas: {total_sales}")
    
    if total_sales >= 50:
        print("\n✅ Datos suficientes para pruebas ML!")
        return True
    else:
        print("\n⚠️ Pocos datos para ML robusto, pero suficiente para testing")
        return True

if __name__ == "__main__":
    create_test_data()
