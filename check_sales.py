#!/usr/bin/env python3
"""
Script para verificar Sales específicas
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
sys.path.append('/Users/juandiegogutierrezcortez/mvp')
django.setup()

from authentication.models import Company
from inventory.models import Product, Sale
from django.utils import timezone
from datetime import timedelta

def check_sales_details():
    """Verificar detalles específicos de las Sales"""
    print("🔍 VERIFICANDO SALES DETALLADAS")
    print("=" * 50)
    
    # Obtener company de prueba
    company = Company.objects.filter(name__icontains='test').first()
    if not company:
        print("❌ No se encontró company de prueba")
        return
    
    print(f"🎯 Company: {company.name}")
    
    # Obtener productos de esta company
    products = Product.objects.filter(company=company)
    print(f"📦 Productos: {products.count()}")
    
    for product in products:
        print(f"\n  📋 Producto: {product.name} (ID: {product.id})")
        
        # Obtener todas las sales de este producto
        all_sales = Sale.objects.filter(product=product)
        print(f"    Total Sales: {all_sales.count()}")
        
        if all_sales.exists():
            print("    Detalles de Sales:")
            for sale in all_sales:
                print(f"      - Fecha: {sale.date_sold}")
                print(f"        Cantidad: {sale.quantity}")
                print(f"        Precio: {sale.unit_price}")
                print(f"        Cliente: {sale.customer_name}")
                # Verificar si tiene total_price o calcularlo
                try:
                    total = sale.total_price
                except AttributeError:
                    total = sale.quantity * sale.unit_price
                print(f"        Total: {total}")
                print()
        
        # Probar el método _get_demand_statistics manualmente
        print("    🧪 Probando _get_demand_statistics...")
        
        # Simular el método
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        
        print(f"    Rango de fechas: {start_date} a {end_date}")
        
        sales_in_range = Sale.objects.filter(
            product=product,
            date_sold__range=[start_date, end_date]
        )
        
        print(f"    Sales en rango: {sales_in_range.count()}")
        
        if sales_in_range.exists():
            # Calcular estadísticas manualmente
            from django.db.models import Sum
            
            daily_demand = sales_in_range.extra(
                select={'date': 'DATE(date_sold)'}
            ).values('date').annotate(
                total_demand=Sum('quantity')
            )
            
            demands = [float(item['total_demand']) for item in daily_demand if item['total_demand'] is not None]
            
            import numpy as np
            average_demand = np.mean(demands) if demands else 0
            
            print(f"    Demanda promedio calculada: {average_demand}")
            print(f"    Días con demanda: {len(demands)}")
            print(f"    Demandas por día: {demands}")
        else:
            print("    ❌ No hay sales en el rango de fechas")

def test_service_directly():
    """Probar el servicio directamente"""
    print("\n" + "=" * 50)
    print("🧪 PROBANDO SERVICIO DIRECTAMENTE")
    print("=" * 50)
    
    company = Company.objects.filter(name__icontains='test').first()
    if not company:
        print("❌ No se encontró company de prueba")
        return
    
    from forecasting.services.inventory_optimization_service import InventoryOptimizationService
    
    service = InventoryOptimizationService(company)
    
    products = Product.objects.filter(company=company)
    
    for product in products:
        print(f"\n📋 Producto: {product.name}")
        
        # Llamar al método directamente
        demand_stats = service._get_demand_statistics(product)
        
        print(f"  Estadísticas de demanda:")
        print(f"    - Demanda promedio: {demand_stats['average_demand']}")
        print(f"    - Variabilidad: {demand_stats['demand_variability']}")
        print(f"    - Lead time variability: {demand_stats['lead_time_variability']}")

if __name__ == '__main__':
    check_sales_details()
    test_service_directly()
