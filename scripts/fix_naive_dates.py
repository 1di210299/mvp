#!/usr/bin/env python
"""
Script para corregir las fechas naive en las transacciones y otros modelos
"""
import os
import sys
import django
from datetime import datetime
from django.utils import timezone
from django.db import transaction

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from inventory.models import Transaction, Sale, InventoryHistory

def fix_naive_datetimes():
    """Corregir todas las fechas naive en el sistema"""
    print("🔧 CORRIGIENDO FECHAS NAIVE...")
    
    # Configurar zona horaria por defecto (UTC)
    default_tz = timezone.get_default_timezone()
    
    with transaction.atomic():
        # Corregir transacciones
        naive_transactions = Transaction.objects.filter(transaction_date__isnull=False)
        updated_transactions = 0
        
        for trans in naive_transactions:
            if trans.transaction_date and timezone.is_naive(trans.transaction_date):
                # Convertir fecha naive a aware usando la zona horaria por defecto
                aware_datetime = timezone.make_aware(trans.transaction_date, default_tz)
                trans.transaction_date = aware_datetime
                trans.save(update_fields=['transaction_date'])
                updated_transactions += 1
        
        print(f"   ✅ Transacciones corregidas: {updated_transactions}")
        
        # Corregir ventas
        naive_sales = Sale.objects.filter(date_sold__isnull=False)
        updated_sales = 0
        
        for sale in naive_sales:
            if sale.date_sold and timezone.is_naive(sale.date_sold):
                aware_datetime = timezone.make_aware(sale.date_sold, default_tz)
                sale.date_sold = aware_datetime
                sale.save(update_fields=['date_sold'])
                updated_sales += 1
        
        print(f"   ✅ Ventas corregidas: {updated_sales}")
        
        # Corregir historial de inventario
        naive_history = InventoryHistory.objects.filter(date_changed__isnull=False)
        updated_history = 0
        
        for hist in naive_history:
            if hist.date_changed and timezone.is_naive(hist.date_changed):
                aware_datetime = timezone.make_aware(hist.date_changed, default_tz)
                hist.date_changed = aware_datetime
                hist.save(update_fields=['date_changed'])
                updated_history += 1
        
        print(f"   ✅ Historial corregido: {updated_history}")
    
    print("✅ Todas las fechas han sido corregidas")

if __name__ == '__main__':
    fix_naive_datetimes()
    print("\n🎉 CORRECCIÓN DE FECHAS COMPLETADA")
    print("📊 RESUMEN:")
    print(f"   💰 Total transacciones: {Transaction.objects.count()}")
    print(f"   💵 Total ventas: {Sale.objects.count()}")
    print(f"   📈 Total historial: {InventoryHistory.objects.count()}")
    print("\n🔑 Credenciales de acceso:")
    print("   📧 Usuario: admin_6789")
    print("   🔐 Contraseña: admin123")
    print("   🏢 Empresa: Distribuidora San Martín SAC")