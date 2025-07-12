#!/usr/bin/env python
"""
Script para limpiar TODOS los datos existentes y crear datos frescos
Esto evita duplicaciones y garantiza consistencia
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from inventory.models import Product, Transaction, InventoryItem, Location
from alerts.models import Alert
from authentication.models import User, Company
from django.utils import timezone

def clean_all_data():
    """Limpiar TODOS los datos existentes"""
    print("🗑️ Limpiando TODOS los datos existentes...")
    
    # Contar datos antes
    transactions_before = Transaction.objects.count()
    inventory_before = InventoryItem.objects.count()
    alerts_before = Alert.objects.count()
    
    print(f"📊 Datos antes de limpiar:")
    print(f"   💰 Transacciones: {transactions_before}")
    print(f"   📦 Inventarios: {inventory_before}")
    print(f"   🚨 Alertas: {alerts_before}")
    
    # Limpiar todo
    Transaction.objects.all().delete()
    InventoryItem.objects.all().delete()
    Alert.objects.all().delete()  # Limpiar todas las alertas
    
    # Verificar limpieza
    transactions_after = Transaction.objects.count()
    inventory_after = InventoryItem.objects.count()
    alerts_after = Alert.objects.count()
    
    print(f"✅ Datos después de limpiar:")
    print(f"   💰 Transacciones: {transactions_after}")
    print(f"   📦 Inventarios: {inventory_after}")
    print(f"   🚨 Alertas: {alerts_after}")
    
    return True

def create_fresh_realistic_data():
    """Crear datos completamente frescos y realistas"""
    print("\n🚀 Creando datos frescos y realistas...")
    
    # Obtener datos necesarios
    products = list(Product.objects.all())
    if not products:
        print("❌ No hay productos. Ejecuta primero el script de productos.")
        return False
    
    location = Location.objects.first()
    if not location:
        location = Location.objects.create(
            name="Almacén Principal",
            address="Av. Principal 123",
            is_active=True
        )
        print(f"📍 Ubicación creada: {location.name}")
    
    user = User.objects.first()
    if not user:
        print("❌ No hay usuarios en la base de datos.")
        return False
    
    print(f"📦 Trabajando con {len(products)} productos")
    
    # Crear transacciones para los últimos 12 meses
    end_date = timezone.now().date()
    total_transactions = 0
    
    for month_offset in range(12):
        month_start = (end_date.replace(day=1) - timedelta(days=30 * month_offset)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_name = month_start.strftime('%B %Y')
        print(f"📅 Mes: {month_name}")
        
        # Patrones realistas por mes
        if month_offset == 0:  # Mes actual (julio)
            sales_qty = random.randint(60, 80)
            purchase_qty = random.randint(25, 35)
        elif month_offset <= 2:  # Últimos 3 meses
            sales_qty = random.randint(70, 100)
            purchase_qty = random.randint(30, 45)
        elif month_offset <= 5:  # Últimos 6 meses
            sales_qty = random.randint(50, 80)
            purchase_qty = random.randint(20, 35)
        else:  # Meses más antiguos
            sales_qty = random.randint(40, 65)
            purchase_qty = random.randint(15, 25)
        
        month_transactions = 0
        
        # Crear VENTAS (cantidades negativas)
        for i in range(sales_qty):
            product = random.choice(products)
            quantity = -random.randint(1, 12)  # Ventas son negativas
            base_cost = float(product.cost_price or 10.0)
            unit_cost = base_cost * random.uniform(1.4, 2.1)  # Precio de venta
            
            # Fecha aleatoria en el mes
            days_in_month = (month_end - month_start).days + 1
            random_day = random.randint(0, days_in_month - 1)
            transaction_date = month_start + timedelta(days=random_day)
            
            Transaction.objects.create(
                product=product,
                quantity=quantity,
                transaction_type='sale',
                unit_cost=Decimal(str(round(unit_cost, 2))),
                transaction_date=transaction_date,
                reference_number=f"VTA-{month_start.strftime('%Y%m')}-{i+1:04d}",
                notes=f"Venta {month_name}",
                location=location,
                created_by=user
            )
            month_transactions += 1
        
        # Crear COMPRAS (cantidades positivas)
        for i in range(purchase_qty):
            product = random.choice(products)
            quantity = random.randint(15, 60)  # Compras son positivas
            base_cost = float(product.cost_price or 10.0)
            unit_cost = base_cost * random.uniform(0.75, 0.95)  # Costo de compra
            
            # Fecha aleatoria en el mes
            days_in_month = (month_end - month_start).days + 1
            random_day = random.randint(0, days_in_month - 1)
            transaction_date = month_start + timedelta(days=random_day)
            
            Transaction.objects.create(
                product=product,
                quantity=quantity,
                transaction_type='purchase',
                unit_cost=Decimal(str(round(unit_cost, 2))),
                transaction_date=transaction_date,
                reference_number=f"COM-{month_start.strftime('%Y%m')}-{i+1:04d}",
                notes=f"Compra {month_name}",
                location=location,
                created_by=user
            )
            month_transactions += 1
        
        total_transactions += month_transactions
        print(f"   ✅ {sales_qty} ventas + {purchase_qty} compras = {month_transactions} transacciones")
    
    print(f"\n🎉 Total de transacciones creadas: {total_transactions}")
    return True

def update_inventories():
    """Actualizar inventarios basado en las transacciones"""
    print("\n🔄 Calculando inventarios finales...")
    
    products = Product.objects.all()
    updated_count = 0
    
    for product in products:
        # Sumar todas las transacciones del producto
        transactions = Transaction.objects.filter(product=product)
        total_quantity = sum(float(t.quantity or 0) for t in transactions)
        
        # El stock final no puede ser negativo
        final_stock = max(0, total_quantity)
        
        # Calcular costo unitario promedio de las últimas compras
        recent_purchases = Transaction.objects.filter(
            product=product,
            transaction_type='purchase'
        ).order_by('-transaction_date')[:5]
        
        if recent_purchases:
            avg_cost = sum(float(t.unit_cost or 0) for t in recent_purchases) / len(recent_purchases)
        else:
            avg_cost = float(product.cost_price or 10.0)
        
        # Obtener ubicación por defecto
        location = Location.objects.first()
        if not location:
            location = Location.objects.create(
                name="Almacén Principal",
                code="ALM001",
                warehouse="Principal",
                is_active=True
            )
        
        # Crear InventoryItem con el stock calculado y unit_cost
        inventory_item = InventoryItem.objects.create(
            product=product,
            location=location,
            quantity=final_stock,
            unit_cost=Decimal(str(round(avg_cost, 4))),
            is_active=True
        )
        
        updated_count += 1
        
        if updated_count % 10 == 0:
            print(f"   ✅ Procesados {updated_count} productos...")
    
    print(f"📦 Inventarios creados: {updated_count} productos")
    return True

def create_realistic_alerts():
    """Crear alertas realistas basadas en el inventario"""
    print("\n🚨 Creando alertas realistas...")
    
    # Obtener la empresa por defecto
    company = Company.objects.first()
    if not company:
        print("❌ No hay empresas en la base de datos.")
        return False
    
    # Buscar productos con stock bajo (menos de 10 unidades)
    low_stock_items = InventoryItem.objects.filter(
        quantity__lt=10,
        quantity__gt=0,
        is_active=True
    ).select_related('product')
    
    alerts_created = 0
    
    for item in low_stock_items[:5]:  # Máximo 5 alertas
        Alert.objects.create(
            company=company,
            title=f"Stock bajo: {item.product.name}",
            message=f"Stock bajo en {item.product.name}: {int(item.quantity)} unidades disponibles",
            severity='medium' if item.quantity >= 5 else 'high',
            status='active',
            product=item.product,
            current_value=item.quantity,
            threshold_value=Decimal('10.0')
        )
        alerts_created += 1
    
    # Crear algunas alertas adicionales para productos sin stock
    products_no_stock = InventoryItem.objects.filter(
        quantity=0,
        is_active=True
    ).select_related('product')[:2]
    
    for item in products_no_stock:
        Alert.objects.create(
            company=company,
            title=f"Producto agotado: {item.product.name}",
            message=f"El producto {item.product.name} está completamente agotado",
            severity='high',
            status='active',
            product=item.product,
            current_value=Decimal('0.0'),
            threshold_value=Decimal('1.0')
        )
        alerts_created += 1
    
    print(f"🚨 Alertas creadas: {alerts_created}")
    return True

def main():
    """Función principal"""
    print("🎯 LIMPIEZA COMPLETA Y CREACIÓN DE DATOS FRESCOS")
    print("=" * 60)
    
    try:
        # Paso 1: Limpiar todo
        if not clean_all_data():
            print("❌ Error en la limpieza")
            return
        
        # Paso 2: Crear transacciones frescas
        if not create_fresh_realistic_data():
            print("❌ Error creando transacciones")
            return
        
        # Paso 3: Actualizar inventarios
        if not update_inventories():
            print("❌ Error actualizando inventarios")
            return
        
        # Paso 4: Crear alertas
        if not create_realistic_alerts():
            print("❌ Error creando alertas")
            return
        
        # Estadísticas finales
        print("\n" + "=" * 60)
        print("🎉 ¡DATOS FRESCOS CREADOS EXITOSAMENTE!")
        print("=" * 60)
        print(f"📊 Estadísticas finales:")
        print(f"   💰 Transacciones: {Transaction.objects.count()}")
        print(f"   📦 Inventarios: {InventoryItem.objects.count()}")
        print(f"   🚨 Alertas: {Alert.objects.count()}")
        print(f"   🛍️ Ventas: {Transaction.objects.filter(transaction_type='sale').count()}")
        print(f"   📥 Compras: {Transaction.objects.filter(transaction_type='purchase').count()}")
        
        print("\n✨ Los gráficos ahora mostrarán datos completamente nuevos y consistentes")
        print("🔄 Actualiza la página de reportes para ver los cambios")
        
    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()