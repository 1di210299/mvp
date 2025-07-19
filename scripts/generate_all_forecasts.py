#!/usr/bin/env python
"""
Script para generar pronósticos para TODOS los productos automáticamente
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from inventory.models import Product
from forecasting.models import DemandForecast
from forecasting.services.forecast_service import ForecastService
from authentication.models import Company

def generate_all_forecasts():
    """Generar pronósticos para TODOS los productos"""
    print("🚀 GENERANDO PRONÓSTICOS PARA TODOS LOS PRODUCTOS")
    print("=" * 60)
    
    try:
        company = Company.objects.get(name="Distribuidora San Martín SAC")
        print(f"✅ Empresa encontrada: {company.name}")
    except Company.DoesNotExist:
        print("❌ ERROR: Empresa no encontrada")
        return
    
    # Obtener todos los productos activos
    products = Product.objects.filter(company=company, is_active=True)
    print(f"📦 Productos activos encontrados: {products.count()}")
    
    if not products.exists():
        print("❌ No hay productos para procesar")
        return
    
    # Limpiar pronósticos antiguos
    old_forecasts = DemandForecast.objects.filter(product__company=company)
    deleted_count = old_forecasts.count()
    old_forecasts.delete()
    print(f"🗑️ Eliminados {deleted_count} pronósticos antiguos")
    
    # Inicializar el servicio de pronósticos
    forecast_service = ForecastService()
    
    total_forecasts = 0
    processed_products = 0
    errors = []
    
    # Generar pronósticos para cada producto
    for i, product in enumerate(products):
        print(f"📈 Procesando producto {i+1}/{products.count()}: {product.name}")
        try:
            # Generar pronósticos para este producto
            forecasts = forecast_service.generate_forecasts(
                product=product,
                forecast_horizon=30,
                include_confidence=True
            )
            
            forecasts_count = len(forecasts)
            total_forecasts += forecasts_count
            processed_products += 1
            
            print(f"  ✅ {forecasts_count} pronósticos creados para {product.name}")
            
        except Exception as e:
            error_msg = f"Error procesando {product.name}: {str(e)}"
            print(f"  ❌ {error_msg}")
            errors.append(error_msg)
            continue
    
    # Resumen final
    print(f"\n🎯 RESUMEN DE GENERACIÓN:")
    print(f"   📦 Productos procesados: {processed_products}/{products.count()}")
    print(f"   📈 Total pronósticos creados: {total_forecasts}")
    print(f"   ✅ Tasa de éxito: {(processed_products/products.count())*100:.1f}%")
    
    if errors:
        print(f"   ⚠️ Errores: {len(errors)}")
        for error in errors[:3]:  # Mostrar solo los primeros 3 errores
            print(f"     • {error}")
    
    # Verificación final
    final_forecasts = DemandForecast.objects.filter(product__company=company)
    unique_products = final_forecasts.values('product').distinct().count()
    
    print(f"\n📊 VERIFICACIÓN FINAL:")
    print(f"   📈 Total pronósticos en BD: {final_forecasts.count()}")
    print(f"   🎯 Productos únicos con pronósticos: {unique_products}/{products.count()}")
    
    return {
        'products_processed': processed_products,
        'total_forecasts': total_forecasts,
        'unique_products_with_forecasts': unique_products,
        'errors': errors
    }

if __name__ == '__main__':
    result = generate_all_forecasts()
    print(f"\n🎉 GENERACIÓN DE PRONÓSTICOS COMPLETADA")
    print(f"💻 Ahora recarga la página de Pronósticos para ver todos los datos")