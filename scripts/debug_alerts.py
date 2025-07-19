#!/usr/bin/env python3
"""
Script de diagnóstico para rastrear errores en el sistema de alertas
"""
import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from alerts.services import AlertService
from alerts.models import AlertRule
from inventory.models import Product, Transaction
from django.utils import timezone
import traceback

def debug_alerts_system():
    """Diagnóstico detallado del sistema de alertas"""
    print("🔍 INICIANDO DIAGNÓSTICO DETALLADO DEL SISTEMA DE ALERTAS")
    print("=" * 80)
    
    # 1. Verificar transacciones con fechas None
    print("\n1. 📅 VERIFICANDO TRANSACCIONES CON FECHAS NONE:")
    transactions_with_none_dates = Transaction.objects.filter(transaction_date__isnull=True)
    print(f"   Total transacciones con fecha None: {transactions_with_none_dates.count()}")
    
    if transactions_with_none_dates.exists():
        print("   Primeras 5 transacciones con fecha None:")
        for i, tx in enumerate(transactions_with_none_dates[:5]):
            print(f"   - ID {tx.id}: {tx.product.name if tx.product else 'Sin producto'} | Tipo: {tx.transaction_type} | Fecha: {tx.transaction_date}")
    
    # 2. Verificar reglas activas
    print("\n2. 📋 VERIFICANDO REGLAS ACTIVAS:")
    active_rules = AlertRule.objects.filter(is_active=True)
    print(f"   Total reglas activas: {active_rules.count()}")
    
    for rule in active_rules:
        print(f"   - Regla ID {rule.id}: {rule.name} | Tipo: {rule.alert_type}")
    
    # 3. Intentar ejecutar cada función con logging detallado
    print("\n3. 🧪 PROBANDO FUNCIONES ESPECÍFICAS:")
    
    alert_service = AlertService()
    
    # Obtener un producto de ejemplo
    test_product = Product.objects.filter(is_active=True).first()
    if not test_product:
        print("   ❌ No hay productos activos para probar")
        return
    
    print(f"   Producto de prueba: {test_product.name} (ID: {test_product.id})")
    
    # Probar cada función individualmente
    test_functions = [
        ('_check_low_stock', 'low_stock'),
        ('_check_high_stock', 'high_stock'),  
        ('_check_no_movement', 'no_movement'),
        ('_check_negative_stock', 'negative_stock'),
        ('_check_high_demand', 'high_demand'),
    ]
    
    # Crear una regla de prueba para cada tipo
    for func_name, rule_type in test_functions:
        print(f"\n   🔧 Probando función: {func_name}")
        
        try:
            # Crear regla temporal para la prueba
            test_rule = AlertRule(
                name=f"Test {rule_type}",
                alert_type=rule_type,
                company=test_product.company,
                threshold_value=10,
                is_active=True
            )
            
            # Obtener la función del servicio
            func = getattr(alert_service, func_name)
            
            print(f"      - Ejecutando {func_name}({test_rule.name}, {test_product.name})...")
            
            # Ejecutar con manejo de errores detallado
            result = func(test_rule, test_product)
            print(f"      ✅ Resultado: {result}")
            
        except Exception as e:
            print(f"      ❌ ERROR en {func_name}:")
            print(f"         Tipo de error: {type(e).__name__}")
            print(f"         Mensaje: {str(e)}")
            print(f"         Traceback completo:")
            
            # Imprimir el traceback completo con números de línea
            tb_lines = traceback.format_exc().split('\n')
            for line_num, line in enumerate(tb_lines, 1):
                if line.strip():
                    print(f"         {line_num:2d}: {line}")
    
    # 4. Probar la función principal
    print(f"\n4. 🎯 PROBANDO FUNCIÓN PRINCIPAL check_all_alerts_sync:")
    
    try:
        print("   Ejecutando check_all_alerts_sync()...")
        result = alert_service.check_all_alerts_sync()
        print(f"   ✅ Resultado exitoso: {result}")
        
    except Exception as e:
        print(f"   ❌ ERROR en check_all_alerts_sync:")
        print(f"      Tipo de error: {type(e).__name__}")
        print(f"      Mensaje: {str(e)}")
        print(f"      Traceback completo:")
        
        tb_lines = traceback.format_exc().split('\n')
        for line_num, line in enumerate(tb_lines, 1):
            if line.strip():
                print(f"      {line_num:2d}: {line}")
    
    print("\n" + "=" * 80)
    print("🏁 DIAGNÓSTICO COMPLETADO")

if __name__ == "__main__":
    debug_alerts_system()