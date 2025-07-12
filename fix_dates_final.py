#!/usr/bin/env python
"""
Script FINAL para crear datos con fechas distribuidas correctamente
Este script resuelve el problema de las fechas concentradas en julio 2025
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

def main():
    """Función principal para crear datos distribuidos correctamente"""
    print("🎯 SCRIPT FINAL: DATOS CON FECHAS DISTRIBUIDAS")
    print("=" * 60)
    
    try:
        # Paso 1: Limpiar transacciones existentes (conservar productos)
        print("🗑️ Limpiando transacciones existentes...")
        Transaction.objects.all().delete()
        InventoryItem.objects.all().delete()
        Alert.objects.all().delete()
        print("✅ Datos anteriores eliminados")
        
        # Paso 2: Obtener datos necesarios
        products = list(Product.objects.all())
        if not products:
            print("❌ No hay productos en la base de datos.")
            return False
        
        location = Location.objects.first()
        if not location:
            location = Location.objects.create(
                name="Almacén Principal",
                code="ALM001",
                warehouse="Principal",
                is_active=True
            )
        
        user = User.objects.first()
        company = Company.objects.first()
        
        print(f"📦 Trabajando con {len(products)} productos")
        
        # Paso 3: Crear transacciones con fechas distribuidas CORRECTAMENTE
        end_date = timezone.now()
        total_transactions = 0
        
        # Crear transacciones para cada mes de los últimos 12 meses
        for month_offset in range(12):
            # Calcular fechas del mes actual
            month_date = end_date - timedelta(days=30 * month_offset)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Último día del mes
            if month_start.month == 12:
                next_month = month_start.replace(year=month_start.year + 1, month=1)
            else:
                next_month = month_start.replace(month=month_start.month + 1)
            month_end = next_month - timedelta(days=1)
            month_end = month_end.replace(hour=23, minute=59, second=59)
            
            month_name = month_start.strftime('%B %Y')
            print(f"📅 Creando datos para {month_name}")
            
            # Determinar cantidad de transacciones por mes (patrón realista)
            if month_offset == 0:  # Mes actual
                sales_count = random.randint(40, 60)
                purchase_count = random.randint(15, 25)
            elif month_offset <= 2:  # Últimos 3 meses
                sales_count = random.randint(60, 85)
                purchase_count = random.randint(25, 35)
            elif month_offset <= 5:  # Últimos 6 meses  
                sales_count = random.randint(50, 75)
                purchase_count = random.randint(20, 30)
            else:  # Meses más antiguos
                sales_count = random.randint(35, 55)
                purchase_count = random.randint(15, 22)
            
            month_transactions = 0
            
            # Crear VENTAS para este mes
            for i in range(sales_count):
                product = random.choice(products)
                quantity = -random.randint(1, 10)  # Ventas negativas
                base_cost = float(product.cost_price or 10.0)
                unit_cost = base_cost * random.uniform(1.5, 2.3)  # Precio de venta
                
                # Fecha aleatoria DENTRO del mes específico
                days_in_month = (month_end.date() - month_start.date()).days + 1
                random_day = random.randint(0, days_in_month - 1)
                random_hour = random.randint(8, 18)  # Horario comercial
                random_minute = random.randint(0, 59)
                
                transaction_date = month_start + timedelta(
                    days=random_day, 
                    hours=random_hour, 
                    minutes=random_minute
                )
                
                # IMPORTANTE: Especificar transaction_date explícitamente
                Transaction.objects.create(
                    product=product,
                    quantity=quantity,
                    transaction_type='sale',
                    unit_cost=Decimal(str(round(unit_cost, 2))),
                    transaction_date=transaction_date,  # Fecha específica del mes
                    reference_number=f"VTA-{month_start.strftime('%Y%m')}-{i+1:04d}",
                    notes=f"Venta {month_name}",
                    location=location,
                    created_by=user
                )
                month_transactions += 1
            
            # Crear COMPRAS para este mes
            for i in range(purchase_count):
                product = random.choice(products)
                quantity = random.randint(20, 80)  # Compras positivas
                base_cost = float(product.cost_price or 10.0)
                unit_cost = base_cost * random.uniform(0.7, 0.9)  # Costo de compra
                
                # Fecha aleatoria DENTRO del mes específico
                days_in_month = (month_end.date() - month_start.date()).days + 1
                random_day = random.randint(0, days_in_month - 1)
                random_hour = random.randint(9, 17)  # Horario comercial
                random_minute = random.randint(0, 59)
                
                transaction_date = month_start + timedelta(
                    days=random_day, 
                    hours=random_hour, 
                    minutes=random_minute
                )
                
                # IMPORTANTE: Especificar transaction_date explícitamente
                Transaction.objects.create(
                    product=product,
                    quantity=quantity,
                    transaction_type='purchase',
                    unit_cost=Decimal(str(round(unit_cost, 2))),
                    transaction_date=transaction_date,  # Fecha específica del mes
                    reference_number=f"COM-{month_start.strftime('%Y%m')}-{i+1:04d}",
                    notes=f"Compra {month_name}",
                    location=location,
                    created_by=user
                )
                month_transactions += 1
            
            total_transactions += month_transactions
            print(f"   ✅ {sales_count} ventas + {purchase_count} compras = {month_transactions} transacciones")
        
        print(f"\n🎉 Total transacciones creadas: {total_transactions}")
        
        # Paso 4: Actualizar inventarios basado en transacciones
        print("\n🔄 Actualizando inventarios...")
        for product in products:
            total_qty = 0
            recent_cost = float(product.cost_price or 10.0)
            
            # Calcular stock final basado en TODAS las transacciones
            for transaction in Transaction.objects.filter(product=product):
                total_qty += float(transaction.quantity or 0)
                if transaction.transaction_type == 'purchase' and transaction.unit_cost:
                    recent_cost = float(transaction.unit_cost)
            
            final_stock = max(0, total_qty)
            
            # Crear inventario actualizado
            InventoryItem.objects.create(
                product=product,
                location=location,
                quantity=final_stock,
                unit_cost=Decimal(str(round(recent_cost, 4))),
                is_active=True
            )
        
        # Paso 5: Crear alertas basadas en inventario real
        print("\n🚨 Creando alertas...")
        if company:
            alert_count = 0
            low_stock_items = InventoryItem.objects.filter(
                quantity__lt=15,
                is_active=True
            ).select_related('product')[:3]
            
            for item in low_stock_items:
                Alert.objects.create(
                    company=company,
                    title=f"Stock bajo: {item.product.name}",
                    message=f"Stock bajo en {item.product.name}: {int(item.quantity)} unidades",
                    severity='medium' if item.quantity >= 8 else 'high',
                    status='active',
                    product=item.product,
                    current_value=item.quantity,
                    threshold_value=Decimal('15.0')
                )
                alert_count += 1
            
            print(f"🚨 Alertas creadas: {alert_count}")
        
        # Paso 6: Verificar distribución final
        print("\n🔍 Verificando distribución final...")
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        
        monthly_distribution = Transaction.objects.annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        print("📊 Distribución final por mes:")
        for item in monthly_distribution:
            print(f"   {item['month'].strftime('%Y-%m')}: {item['count']} transacciones")
        
        # Estadísticas finales
        print("\n" + "=" * 60)
        print("🎉 ¡DATOS CON FECHAS DISTRIBUIDAS CREADOS!")
        print("=" * 60)
        print(f"📊 Estadísticas finales:")
        print(f"   💰 Transacciones: {Transaction.objects.count()}")
        print(f"   📦 Inventarios: {InventoryItem.objects.count()}")
        print(f"   🚨 Alertas: {Alert.objects.count()}")
        print(f"   🛍️ Ventas: {Transaction.objects.filter(transaction_type='sale').count()}")
        print(f"   📥 Compras: {Transaction.objects.filter(transaction_type='purchase').count()}")
        
        print("\n✨ Los gráficos ahora mostrarán datos distribuidos en 12 meses")
        print("🔄 Actualiza la página de reportes para ver gráficos con sentido")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎯 ¡ÉXITO! Los datos ahora tienen fechas distribuidas correctamente")
    else:
        print("\n❌ Hubo errores en el proceso")