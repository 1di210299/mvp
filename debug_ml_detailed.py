#!/usr/bin/env python3
"""
Script de debug específico para identificar problemas en ML
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
sys.path.append('/Users/juandiegogutierrezcortez/mvp')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from authentication.models import Company
from inventory.models import Product, Transaction
from forecasting.services.inventory_optimization_service import InventoryOptimizationService
from forecasting.services.demand_analysis_service import DemandAnalysisService
from django.utils import timezone
import random

User = get_user_model()

def create_test_demand_data():
    """Crear datos de demanda de prueba"""
    print("🔍 DEBUG: Creando datos de demanda de prueba...")
    
    company = Company.objects.filter(name__icontains='test').first()
    if not company:
        print("❌ No se encontró company de prueba")
        return
    
    products = Product.objects.filter(company=company, is_active=True)
    
    # Crear transacciones de venta para los últimos 60 días
    for product in products:
        print(f"📊 Creando transacciones para {product.name}")
        
        for days_ago in range(60):
            # Crear 1-3 transacciones aleatorias por día
            num_transactions = random.randint(1, 3)
            
            for _ in range(num_transactions):
                quantity = random.randint(1, 10)
                date = timezone.now() - timezone.timedelta(days=days_ago)
                
                Transaction.objects.create(
                    product=product,
                    transaction_type='sale',
                    quantity=quantity,
                    unit_price=float(product.sale_price or 100),
                    total_price=quantity * float(product.sale_price or 100),
                    transaction_date=date,
                    description=f"Test sale for {product.name}"
                )
        
        print(f"✅ Transacciones creadas para {product.name}")
    
    print("✅ Datos de demanda de prueba creados")

def create_test_user():
    """Crear usuario de prueba"""
    print("🔍 DEBUG: Creando usuario de prueba...")
    
    company = Company.objects.filter(name__icontains='test').first()
    if not company:
        print("❌ No se encontró company de prueba")
        return None
    
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'company': company
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print("✅ Usuario de prueba creado")
    else:
        print("✅ Usuario de prueba ya existía")
    
    return user

def debug_inventory_optimization():
    """Debug específico para inventory optimization"""
    print("🔍 DEBUG: Iniciando debug de Inventory Optimization")
    
    # Obtener company de prueba
    company = Company.objects.filter(name__icontains='test').first()
    if not company:
        print("❌ No se encontró company de prueba")
        return
    
    print(f"✅ Company encontrada: {company.name}")
    
    # Verificar productos
    products = Product.objects.filter(company=company, is_active=True)
    print(f"📊 Productos activos: {products.count()}")
    
    for product in products[:3]:  # Solo los primeros 3
        print(f"  - {product.name}: Stock={product.stock}, Precio={product.sale_price}")
    
    # Inicializar servicio
    service = InventoryOptimizationService(company)
    
    # Test calculate_optimal_stock_levels
    print("\n🔍 DEBUG: Calculando niveles óptimos...")
    try:
        stock_levels = service.calculate_optimal_stock_levels()
        print(f"✅ Niveles óptimos calculados: {len(stock_levels)}")
    except Exception as e:
        print(f"❌ Error en calculate_optimal_stock_levels: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test predict_stockouts
    print("\n🔍 DEBUG: Prediciendo stockouts...")
    try:
        predictions = service.predict_stockouts()
        print(f"✅ Predicciones de stockout: {len(predictions)}")
    except Exception as e:
        print(f"❌ Error en predict_stockouts: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test comprehensive_inventory_optimization
    print("\n🔍 DEBUG: Optimización completa...")
    try:
        result = service.comprehensive_inventory_optimization(company)
        print(f"✅ Optimización completa exitosa")
        print(f"  - Stock levels: {len(result.get('stock_levels', []))}")
        print(f"  - Stockout predictions: {len(result.get('stockout_predictions', []))}")
        print(f"  - ABC analysis: {result.get('abc_analysis', {}).get('classification_counts', {})}")
    except Exception as e:
        print(f"❌ Error en comprehensive_inventory_optimization: {str(e)}")
        import traceback
        traceback.print_exc()

def debug_demand_forecasting():
    """Debug específico para demand forecasting"""
    print("\n🔍 DEBUG: Iniciando debug de Demand Forecasting")
    
    # Obtener company de prueba
    company = Company.objects.filter(name__icontains='test').first()
    if not company:
        print("❌ No se encontró company de prueba")
        return
    
    print(f"✅ Company encontrada: {company.name}")
    
    # Verificar productos
    products = Product.objects.filter(company=company, is_active=True)
    print(f"📊 Productos activos: {products.count()}")
    
    # Inicializar servicio
    service = DemandAnalysisService(company)
    
    # Test analyze_seasonal_patterns
    print("\n🔍 DEBUG: Analizando patrones estacionales...")
    try:
        patterns = service.analyze_seasonal_patterns()
        print(f"✅ Patrones estacionales analizados: {len(patterns)}")
        
        for pattern in patterns[:2]:  # Solo los primeros 2
            print(f"  - {pattern.product.name}: Strength={pattern.pattern_strength}")
    except Exception as e:
        print(f"❌ Error en analyze_seasonal_patterns: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Verificar DemandPattern en la DB
    from forecasting.models import DemandPattern
    demand_patterns = DemandPattern.objects.filter(product__company=company)
    print(f"📊 DemandPattern en DB: {demand_patterns.count()}")

def debug_endpoint_calls():
    """Debug específico para llamadas a endpoints"""
    print("\n🔍 DEBUG: Iniciando debug de endpoints")
    
    # Crear cliente de prueba
    client = Client()
    
    # Crear/obtener usuario de prueba
    user = create_test_user()
    if not user:
        print("❌ No se pudo crear usuario de prueba")
        return
    
    client.force_login(user)
    
    # Test inventory optimization endpoint
    print("\n🔍 DEBUG: Probando endpoint de inventory optimization")
    try:
        response = client.get('/api/forecasting/inventory/optimization/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Data: {data}")
        else:
            print(f"Error content: {response.content}")
    except Exception as e:
        print(f"❌ Error en endpoint inventory optimization: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test demand patterns endpoint
    print("\n🔍 DEBUG: Probando endpoint de demand patterns")
    try:
        response = client.get('/api/forecasting/demand/patterns/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Data: {data}")
        else:
            print(f"Error content: {response.content}")
    except Exception as e:
        print(f"❌ Error en endpoint demand patterns: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🚀 INICIANDO DEBUG DETALLADO DE FUNCIONALIDADES ML")
    print("=" * 80)
    
    # PRIMERO: Crear datos de demanda de prueba
    create_test_demand_data()
    
    debug_inventory_optimization()
    debug_demand_forecasting()
    debug_endpoint_calls()
    
    print("\n" + "=" * 80)
    print("🔍 DEBUG COMPLETADO")
