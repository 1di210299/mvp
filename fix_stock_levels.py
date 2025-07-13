#!/usr/bin/env python
"""
Script para ajustar stocks y hacer que el sistema genere recomendaciones reales
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from inventory.models import InventoryItem, Product, Location, Transaction
from authentication.models import Company

def fix_stock_levels():
    """Ajustar niveles de stock para generar recomendaciones"""
    print("🔧 AJUSTANDO NIVELES DE STOCK PARA GENERAR RECOMENDACIONES")
    print("=" * 70)
    
    try:
        company = Company.objects.get(name="Distribuidora San Martín SAC")
        print(f"✅ Empresa encontrada: {company.name}")
    except Company.DoesNotExist:
        print("❌ ERROR: Empresa no encontrada")
        return
    
    # Obtener todos los items de inventario
    inventory_items = InventoryItem.objects.filter(product__company=company)
    print(f"📦 Items de inventario encontrados: {inventory_items.count()}")
    
    if not inventory_items.exists():
        print("❌ No hay items de inventario para ajustar")
        return
    
    # Seleccionar items para reducir stock (aproximadamente 30% de ellos)
    total_items = inventory_items.count()
    items_to_reduce = int(total_items * 0.3)  # 30% de los items
    
    print(f"🎯 Reduciendo stock en {items_to_reduce} de {total_items} items")
    
    items_adjusted = 0
    recommendations_expected = 0
    
    with transaction.atomic():
        # FIX: Usar 'quantity' en lugar de 'current_stock'
        high_stock_items = inventory_items.filter(
            quantity__gt=50  # Solo items con stock mayor a 50
        ).order_by('-quantity')[:items_to_reduce]
        
        for item in high_stock_items:
            old_stock = float(item.quantity)
            
            # Reducir stock a un nivel crítico (5-20 unidades)
            import random
            new_stock = random.uniform(5, 20)
            
            # Crear transacción de ajuste de salida para registrar el cambio
            adjustment_quantity = old_stock - new_stock
            
            Transaction.objects.create(
                product=item.product,
                location=item.location,
                transaction_type='adjustment_out',
                quantity=Decimal(str(adjustment_quantity)),
                transaction_date=timezone.now(),
                notes=f"Ajuste para simulación de stock bajo - Stock anterior: {old_stock:.1f}"
            )
            
            # FIX: Actualizar el campo correcto 'quantity'
            item.quantity = Decimal(str(new_stock))
            item.save()
            
            print(f"   📉 {item.product.name} en {item.location.name}: {old_stock:.1f} → {new_stock:.1f}")
            items_adjusted += 1
            recommendations_expected += 1
    
    print(f"✅ {items_adjusted} items ajustados")
    print(f"🎯 Se esperan aproximadamente {recommendations_expected} recomendaciones")
    
    # Verificar algunos stocks específicos
    print(f"\n📊 VERIFICACIÓN DE STOCKS BAJOS:")
    low_stock_items = InventoryItem.objects.filter(
        product__company=company,
        quantity__lt=30  # FIX: Usar 'quantity'
    ).order_by('quantity')[:10]
    
    for item in low_stock_items:
        print(f"   ⚠️ {item.product.name}: {item.quantity} en {item.location.name}")
    
    return items_adjusted

if __name__ == '__main__':
    result = fix_stock_levels()
    print(f"\n🎉 AJUSTE DE STOCKS COMPLETADO")
    print(f"💡 Ahora el sistema debería generar recomendaciones reales")
    print(f"🔄 Ejecuta el endpoint de generar recomendaciones para ver los resultados")