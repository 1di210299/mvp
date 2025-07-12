#!/usr/bin/env python
"""
Script para crear transacciones más diversas y corregir fechas
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
from inventory.models import Product, Transaction, Location

User = get_user_model()

def create_diverse_transactions():
    """Crear transacciones más diversas con fechas correctas"""
    print("🔄 Creando transacciones diversas...")
    
    # Limpiar transacciones existentes
    Transaction.objects.all().delete()
    print("✅ Transacciones anteriores eliminadas")
    
    # Obtener datos necesarios
    user = User.objects.first()
    products = list(Product.objects.all())
    locations = list(Location.objects.all())
    
    if not products:
        print("❌ No hay productos en la base de datos")
        return
    
    if not locations:
        print("❌ No hay ubicaciones en la base de datos")
        return
    
    print(f"📦 Productos disponibles: {len(products)}")
    print(f"🏪 Ubicaciones disponibles: {len(locations)}")
    
    transactions_created = 0
    
    # Crear transacciones para los últimos 30 días
    start_date = timezone.now() - timedelta(days=30)
    
    # Distribuir transacciones por todos los productos
    for day in range(30):
        current_date = start_date + timedelta(days=day)
        
        # 5-10 transacciones por día
        daily_transactions = random.randint(5, 10)
        
        for i in range(daily_transactions):
            # Seleccionar producto y ubicación aleatoriamente
            product = random.choice(products)
            location = random.choice(locations)
            
            # Tipo de transacción
            transaction_type = random.choice(['purchase', 'sale', 'adjustment'])
            
            # Calcular cantidad y costo según el tipo
            if transaction_type == 'purchase':
                quantity = Decimal(str(random.randint(50, 200)))
                unit_cost = product.cost_price
                notes = f'Compra a {product.supplier.name}' if product.supplier else 'Compra a proveedor'
                reference = f'COMP-{random.randint(10000, 99999)}'
            elif transaction_type == 'sale':
                quantity = Decimal(str(-random.randint(1, 30)))  # Negativo para ventas
                unit_cost = None
                notes = 'Venta a cliente'
                reference = f'VENT-{random.randint(10000, 99999)}'
            else:  # adjustment
                quantity = Decimal(str(random.randint(-20, 20)))
                unit_cost = product.cost_price if quantity > 0 else None
                notes = 'Ajuste de inventario'
                reference = f'AJU-{random.randint(10000, 99999)}'
            
            # Crear la transacción con fecha específica
            transaction_date = current_date + timedelta(
                hours=random.randint(8, 18),
                minutes=random.randint(0, 59)
            )
            
            Transaction.objects.create(
                product=product,
                location=location,
                transaction_type=transaction_type,
                quantity=quantity,
                unit_cost=unit_cost,
                reference_number=reference,
                notes=notes,
                transaction_date=transaction_date,
                created_by=user
            )
            transactions_created += 1
    
    print(f"✅ {transactions_created} transacciones diversas creadas")
    
    # Verificar la diversidad
    from collections import Counter
    products_with_transactions = Transaction.objects.values_list('product__name', flat=True)
    product_counts = Counter(products_with_transactions)
    
    print(f"\n📊 Resumen de diversidad:")
    print(f"   - Total productos con transacciones: {len(product_counts)}")
    print(f"   - Total transacciones: {transactions_created}")
    
    print(f"\n🔝 Top 10 productos con más transacciones:")
    for product, count in product_counts.most_common(10):
        print(f"   - {product}: {count} transacciones")
    
    # Verificar tipos de transacciones
    transaction_types = Transaction.objects.values_list('transaction_type', flat=True)
    type_counts = Counter(transaction_types)
    
    print(f"\n📈 Tipos de transacciones:")
    for trans_type, count in type_counts.items():
        print(f"   - {trans_type}: {count} transacciones")

if __name__ == '__main__':
    create_diverse_transactions()