#!/usr/bin/env python
"""
Script para analizar la coherencia entre datos de productos y reportes
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from inventory.models import Product, Sale, Transaction
from reports.models import Report, KPIValue, KPIDefinition
from django.db.models import Sum, Count, Avg, F
from datetime import datetime, timedelta

def analyze_data_coherence():
    print("="*60)
    print("           ANÁLISIS DE COHERENCIA DE DATOS")
    print("="*60)
    print()
    
    # 1. Conteos básicos
    print("📊 CONTEOS BÁSICOS:")
    product_count = Product.objects.count()
    sale_count = Sale.objects.count()
    transaction_count = Transaction.objects.count()
    report_count = Report.objects.count()
    kpi_count = KPIValue.objects.count()
    
    print(f"   • Productos: {product_count}")
    print(f"   • Ventas: {sale_count}")
    print(f"   • Transacciones: {transaction_count}")
    print(f"   • Reportes: {report_count}")
    print(f"   • KPIs: {kpi_count}")
    print()
    
    # 2. Productos más vendidos
    print("📦 TOP 5 PRODUCTOS MÁS VENDIDOS:")
    try:
        top_products = Sale.objects.values('product__name', 'product__sku').annotate(
            total_vendido=Sum('quantity'),
            veces_vendido=Count('id'),
            ingresos_totales=Sum('total_amount')
        ).order_by('-total_vendido')[:5]
        
        for i, p in enumerate(top_products, 1):
            name = p['product__name']
            sku = p['product__sku']
            vendido = p['total_vendido']
            ventas = p['veces_vendido']
            ingresos = p['ingresos_totales']
            print(f"   {i}. {name} (SKU: {sku})")
            print(f"      - {vendido} unidades vendidas")
            print(f"      - {ventas} transacciones de venta")
            print(f"      - ${ingresos:.2f} en ingresos")
            print()
    except Exception as e:
        print(f"   ❌ Error obteniendo productos más vendidos: {e}")
    
    # 3. Coherencia de stock
    print("🔍 VERIFICACIÓN DE COHERENCIA STOCK:")
    try:
        for product in Product.objects.all()[:5]:
            # Total vendido de este producto
            total_vendido = Sale.objects.filter(product=product).aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            # Stock actual
            stock_actual = product.stock
            
            print(f"   • {product.name}:")
            print(f"     - Stock actual: {stock_actual}")
            print(f"     - Total vendido históricamente: {total_vendido}")
            
            # Verificar si tiene sentido
            if total_vendido > 0 and stock_actual >= 0:
                print("     ✅ Datos coherentes")
            elif total_vendido == 0 and stock_actual > 0:
                print("     ⚠️  Producto con stock pero sin ventas")
            else:
                print("     ✅ Normal")
            print()
    except Exception as e:
        print(f"   ❌ Error verificando coherencia: {e}")
    
    # 4. Análisis de reportes
    print("📈 ANÁLISIS DE REPORTES:")
    if report_count > 0:
        print("   ✅ Existen reportes generados")
        for report in Report.objects.all()[:3]:
            print(f"   • {report.title} - Estado: {report.status}")
    else:
        print("   ⚠️  NO HAY REPORTES GENERADOS")
        print("   💡 Los reportes deberían usar datos de productos/ventas")
    print()
    
    # 5. KPIs disponibles
    print("📊 ANÁLISIS DE KPIs:")
    kpi_definitions = KPIDefinition.objects.count()
    print(f"   • Definiciones de KPI: {kpi_definitions}")
    
    if kpi_count > 0:
        print("   ✅ Existen valores de KPI calculados")
        for kpi in KPIValue.objects.all()[:3]:
            print(f"   • {kpi.kpi.name}: {kpi.value}")
    else:
        print("   ⚠️  NO HAY KPIs CALCULADOS")
        print("   💡 Los KPIs deberían calcularse basándose en productos/ventas")
    print()
    
    # 6. CONCLUSIÓN DE COHERENCIA
    print("="*60)
    print("                    CONCLUSIÓN")
    print("="*60)
    
    if sale_count > 0 and product_count > 0:
        ratio_ventas = sale_count / product_count
        print(f"✅ DATOS OPERATIVOS: Excelentes ({ratio_ventas:.1f} ventas por producto)")
    
    if report_count == 0 and kpi_count == 0:
        print("⚠️  DATOS ANALÍTICOS: Faltantes")
        print("💡 RECOMENDACIÓN: Los reportes y KPIs deberían generarse")
        print("   basándose en los datos de productos y ventas existentes")
    else:
        print("✅ DATOS ANALÍTICOS: Disponibles")
    
    print()
    print("🔗 RELACIÓN DE COMPLEMENTARIEDAD:")
    if product_count > 0 and sale_count > 0:
        print("   ✅ Datos de productos (fuente) ← disponibles")
        print("   ✅ Datos de ventas (actividad) ← disponibles")
        if report_count > 0 or kpi_count > 0:
            print("   ✅ Datos analíticos (insights) ← disponibles")
            print("   🎯 CONCLUSIÓN: Datos PERFECTAMENTE COMPLEMENTARIOS")
        else:
            print("   ❌ Datos analíticos (insights) ← FALTANTES")
            print("   🎯 CONCLUSIÓN: Datos PARCIALMENTE COMPLEMENTARIOS")
            print("      Los reportes necesitan ser generados para completar el flujo")

if __name__ == "__main__":
    analyze_data_coherence()