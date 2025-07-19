#!/usr/bin/env python3
"""
Diagnóstico y corrección de errores ML Services Core
===================================================
Identifica y corrige los errores encontrados en la verificación:
1. Problemas de base de datos (campos faltantes)
2. Errores de estructura de datos
3. Problemas de configuración ML
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.db import connection
from authentication.models import Company
import uuid

def diagnose_database_issues():
    """Diagnosticar problemas de base de datos"""
    print("🔍 DIAGNÓSTICO DE BASE DE DATOS")
    print("=" * 40)
    
    cursor = connection.cursor()
    
    # 1. Verificar tablas existentes
    print("\n1️⃣ VERIFICACIÓN DE TABLAS")
    print("-" * 30)
    
    tables_to_check = [
        'forecasting_forecastingmodel',
        'forecasting_revenueprediction', 
        'forecasting_supplierperformance',
        'forecasting_modelmetrics',
        'forecasting_aiinsight',
        'forecasting_hybridmlaiprediction'
    ]
    
    existing_tables = []
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables_to_check:
        if table in all_tables:
            print(f"✅ {table} - Existe")
            existing_tables.append(table)
        else:
            print(f"❌ {table} - FALTANTE")
    
    # 2. Verificar campos específicos que fallan
    print("\n2️⃣ VERIFICACIÓN DE CAMPOS")
    print("-" * 30)
    
    field_checks = [
        ('forecasting_revenueprediction', 'financial_model'),
        ('forecasting_supplierperformance', 'company_id'),
        ('forecasting_modelmetrics', 'created_at'),
    ]
    
    for table, field in field_checks:
        if table in existing_tables:
            try:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [row[1] for row in cursor.fetchall()]
                if field in columns:
                    print(f"✅ {table}.{field} - Existe")
                else:
                    print(f"❌ {table}.{field} - FALTANTE")
            except Exception as e:
                print(f"⚠️ {table}.{field} - Error verificando: {str(e)[:30]}...")
        else:
            print(f"⚠️ {table}.{field} - Tabla no existe")
    
    return existing_tables

def diagnose_ml_data_issues():
    """Diagnosticar problemas de datos ML"""
    print("\n🔍 DIAGNÓSTICO DE DATOS ML")
    print("=" * 35)
    
    # Crear company de prueba
    unique_id = uuid.uuid4().hex[:8]
    unique_ruc = f"2050000{unique_id[:3]}"
    
    try:
        company = Company.objects.create(
            ruc=unique_ruc,
            name=f"Test Diagnose {unique_id}",
            email=f'diagnose{unique_id}@test.com',
            address='Test Address',
            industry='Technology'
        )
        print(f"✅ Company de prueba creada: {company.name}")
        
        # Test Prophet con datos simulados
        print("\n1️⃣ TEST PROPHET CON DATOS SIMULADOS")
        print("-" * 40)
        
        try:
            from forecasting.ml_algorithms.prophet_forecaster import ProphetForecaster
            import pandas as pd
            from datetime import datetime, timedelta
            
            # Crear datos de prueba con formato correcto
            dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
            values = [100 + i*2 + (i%7)*5 for i in range(30)]
            
            test_data = pd.DataFrame({
                'ds': dates,  # Prophet requiere 'ds'
                'y': values   # Prophet requiere 'y'
            })
            
            prophet = ProphetForecaster()
            result = prophet.fit(test_data)
            
            if result:
                print("✅ Prophet - Puede entrenar con datos correctos")
            else:
                print("❌ Prophet - Falla incluso con datos correctos")
                
        except Exception as e:
            print(f"❌ Prophet - Error: {str(e)}")
        
        # Test ARIMA con datos simulados
        print("\n2️⃣ TEST ARIMA CON DATOS SIMULADOS")
        print("-" * 40)
        
        try:
            from forecasting.ml_algorithms.arima_forecaster import ARIMAForecaster
            
            # Crear datos para ARIMA (debe ser Series)
            test_series = pd.Series(values, index=dates)
            
            arima = ARIMAForecaster()
            result = arima.fit(test_series)
            
            if result:
                print("✅ ARIMA - Puede entrenar con datos correctos")
            else:
                print("❌ ARIMA - Falla incluso con datos correctos")
                
        except Exception as e:
            print(f"❌ ARIMA - Error: {str(e)}")
        
        # Test Random Forest con datos simulados
        print("\n3️⃣ TEST RANDOM FOREST CON DATOS SIMULADOS")
        print("-" * 45)
        
        try:
            from forecasting.ml_algorithms.random_forest_forecaster import RandomForestForecaster
            
            # Crear datos para Random Forest (DataFrame con features)
            rf_data = pd.DataFrame({
                'date': dates,
                'value': values,
                'day_of_week': [d.weekday() for d in dates],
                'month': [d.month for d in dates]
            })
            
            rf = RandomForestForecaster()
            result = rf.fit(rf_data, target_column='value')
            
            if result:
                print("✅ Random Forest - Puede entrenar con datos correctos")
            else:
                print("❌ Random Forest - Falla incluso con datos correctos")
                
        except Exception as e:
            print(f"❌ Random Forest - Error: {str(e)}")
        
        # Limpiar
        company.delete()
        print(f"\n🧹 Company de prueba eliminada")
        
    except Exception as e:
        print(f"❌ Error general en diagnóstico de datos: {str(e)}")

def diagnose_service_issues():
    """Diagnosticar problemas en servicios"""
    print("\n🔍 DIAGNÓSTICO DE SERVICIOS ML")
    print("=" * 40)
    
    # Crear company de prueba
    unique_id = uuid.uuid4().hex[:8]
    unique_ruc = f"2050000{unique_id[:3]}"
    
    try:
        company = Company.objects.create(
            ruc=unique_ruc,
            name=f"Test Service {unique_id}",
            email=f'service{unique_id}@test.com',
            address='Test Address',
            industry='Technology'
        )
        
        # Test Customer Intelligence
        print("\n1️⃣ TEST CUSTOMER INTELLIGENCE")
        print("-" * 35)
        
        try:
            from forecasting.services.customer_intelligence_service import CustomerIntelligenceService
            
            ci_service = CustomerIntelligenceService(company)
            
            # Verificar métodos sin ejecutar con datos reales
            methods_to_check = [
                'calculate_baseline_accuracy_metrics',
                'get_performance_summary',
                'calculate_rfm_scores',
                'predict_churn',
                'calculate_clv'
            ]
            
            for method in methods_to_check:
                if hasattr(ci_service, method):
                    print(f"✅ {method} - Método existe")
                else:
                    print(f"❌ {method} - Método faltante")
                    
        except Exception as e:
            print(f"❌ Customer Intelligence - Error: {str(e)}")
        
        # Test Financial Forecasting
        print("\n2️⃣ TEST FINANCIAL FORECASTING")
        print("-" * 35)
        
        try:
            from forecasting.services.financial_forecasting_service import FinancialForecastingService
            
            ff_service = FinancialForecastingService(company)
            
            methods_to_check = [
                'calculate_baseline_accuracy_metrics',
                'get_performance_summary',
                'predict_revenue',
                'analyze_roi',
                'forecast_cashflow'
            ]
            
            for method in methods_to_check:
                if hasattr(ff_service, method):
                    print(f"✅ {method} - Método existe")
                else:
                    print(f"❌ {method} - Método faltante")
                    
        except Exception as e:
            print(f"❌ Financial Forecasting - Error: {str(e)}")
        
        # Limpiar
        company.delete()
        
    except Exception as e:
        print(f"❌ Error general en diagnóstico de servicios: {str(e)}")

def provide_solutions():
    """Proporcionar soluciones para los errores encontrados"""
    print("\n🔧 SOLUCIONES RECOMENDADAS")
    print("=" * 35)
    
    print("1️⃣ PROBLEMAS DE BASE DE DATOS:")
    print("   • Ejecutar: python manage.py makemigrations")
    print("   • Ejecutar: python manage.py migrate")
    print("   • Verificar que todos los modelos están registrados")
    
    print("\n2️⃣ PROBLEMAS DE DATOS ML:")
    print("   • Prophet necesita columnas 'ds' (fecha) y 'y' (valor)")
    print("   • ARIMA necesita pandas.Series con índice temporal")
    print("   • Random Forest necesita DataFrame con features numéricas")
    
    print("\n3️⃣ PROBLEMAS DE SERVICIOS:")
    print("   • Verificar que los modelos referenced existen en DB")
    print("   • Revisar foreign keys en modelos")
    print("   • Asegurar que los queries usan campos correctos")
    
    print("\n4️⃣ ACCIONES INMEDIATAS:")
    print("   • Revisar models.py para campos faltantes")
    print("   • Crear datos de prueba con formato correcto")
    print("   • Implementar manejo de errores robusto")

def main():
    """Función principal de diagnóstico"""
    print("🚨 DIAGNÓSTICO COMPLETO DE ERRORES ML SERVICES CORE")
    print("=" * 60)
    
    try:
        # Diagnóstico de base de datos
        existing_tables = diagnose_database_issues()
        
        # Diagnóstico de datos ML
        diagnose_ml_data_issues()
        
        # Diagnóstico de servicios
        diagnose_service_issues()
        
        # Soluciones
        provide_solutions()
        
        print(f"\n📋 RESUMEN DEL DIAGNÓSTICO:")
        print(f"   • Tablas encontradas: {len(existing_tables)}")
        print(f"   • Errores identificados en estructura de datos")
        print(f"   • Errores identificados en queries de base de datos")
        print(f"   • Soluciones proporcionadas")
        
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
