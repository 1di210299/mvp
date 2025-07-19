#!/usr/bin/env python3
"""
Script de verificación para la arquitectura Core ML - Semana 1
Verifica la implementación de:
1. Schema ML tradicional (RFM, CLV, Churn scores)
2. Schema AI insights (sentiment, strategy recommendations)
3. Campos para tracking AI API usage y costos
4. Versionado tanto de modelos ML como prompts AI
5. Índices optimizados para ambos tipos de queries
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.db import connection
from django.apps import apps

def check_model_exists(app_label, model_name):
    """Verifica si un modelo existe"""
    try:
        model = apps.get_model(app_label, model_name)
        return True, model
    except LookupError:
        return False, None

def check_database_tables():
    """Verifica las tablas en la base de datos"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
    return tables

def check_indexes():
    """Verifica los índices en la base de datos"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index';")
        indexes = cursor.fetchall()
    return indexes

def verify_ml_architecture():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN DE ARQUITECTURA ML - SEMANA 1")
    print("=" * 50)
    
    # 1. Verificar Schema ML tradicional
    print("\n1️⃣ SCHEMA ML TRADICIONAL")
    print("-" * 30)
    
    ml_models = [
        ('forecasting', 'CustomerLifetimeValue'),
        ('forecasting', 'ChurnPrediction'),
        ('forecasting', 'CustomerSegmentation'),
        ('forecasting', 'MLModelVersion'),
        ('forecasting', 'MLMetric'),
        ('forecasting', 'MLExperiment'),
    ]
    
    for app, model in ml_models:
        exists, model_obj = check_model_exists(app, model)
        status = "✅" if exists else "❌"
        print(f"{status} {model}")
        
        if exists and hasattr(model_obj, '_meta'):
            fields = [f.name for f in model_obj._meta.fields]
            print(f"   Campos: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}")
    
    # 2. Verificar Schema AI insights
    print("\n2️⃣ SCHEMA AI INSIGHTS")
    print("-" * 30)
    
    ai_models = [
        ('forecasting', 'AIPromptVersion'),
        ('forecasting', 'AIAPIUsage'),
        ('forecasting', 'AIInsight'),
        ('forecasting', 'HybridMLAIPrediction'),
    ]
    
    for app, model in ai_models:
        exists, model_obj = check_model_exists(app, model)
        status = "✅" if exists else "❌"
        print(f"{status} {model}")
        
        if exists and hasattr(model_obj, '_meta'):
            fields = [f.name for f in model_obj._meta.fields]
            print(f"   Campos: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}")
    
    # 3. Verificar tablas en base de datos
    print("\n3️⃣ TABLAS EN BASE DE DATOS")
    print("-" * 30)
    
    tables = check_database_tables()
    forecasting_tables = [t for t in tables if 'forecasting' in t]
    
    print(f"Total de tablas: {len(tables)}")
    print(f"Tablas de forecasting: {len(forecasting_tables)}")
    
    for table in sorted(forecasting_tables)[:10]:  # Mostrar primeras 10
        print(f"✅ {table}")
    
    if len(forecasting_tables) > 10:
        print(f"... y {len(forecasting_tables) - 10} más")
    
    # 4. Verificar índices
    print("\n4️⃣ ÍNDICES OPTIMIZADOS")
    print("-" * 30)
    
    indexes = check_indexes()
    forecasting_indexes = [idx for idx in indexes if idx[0] and 'forecasting' in idx[0]]
    
    print(f"Total de índices: {len(indexes)}")
    print(f"Índices de forecasting: {len(forecasting_indexes)}")
    
    for name, sql in forecasting_indexes[:5]:  # Mostrar primeros 5
        print(f"✅ {name}")
        if sql:
            print(f"   SQL: {sql[:80]}{'...' if len(sql) > 80 else ''}")
    
    # 5. Verificar archivos de migración
    print("\n5️⃣ MIGRACIONES")
    print("-" * 30)
    
    migrations_path = Path("forecasting/migrations")
    if migrations_path.exists():
        migration_files = list(migrations_path.glob("*.py"))
        migration_files = [f for f in migration_files if f.name != "__init__.py"]
        
        print(f"Archivos de migración: {len(migration_files)}")
        for migration in sorted(migration_files)[-5:]:  # Últimas 5 migraciones
            print(f"✅ {migration.name}")
    else:
        print("❌ Directorio de migraciones no encontrado")
    
    # 6. Verificar archivos de modelos
    print("\n6️⃣ ARCHIVOS DE MODELOS")
    print("-" * 30)
    
    models_path = Path("forecasting/models")
    if models_path.exists():
        model_files = list(models_path.glob("*.py"))
        
        for model_file in sorted(model_files):
            if model_file.stat().st_size > 0:
                print(f"✅ {model_file.name} ({model_file.stat().st_size} bytes)")
            else:
                print(f"⚠️  {model_file.name} (archivo vacío)")
    else:
        print("❌ Directorio de modelos no encontrado")
    
    # Resumen final
    print("\n📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)
    
    total_ml_models = len([m for m in ml_models if check_model_exists(m[0], m[1])[0]])
    total_ai_models = len([m for m in ai_models if check_model_exists(m[0], m[1])[0]])
    
    print(f"Modelos ML tradicionales: {total_ml_models}/{len(ml_models)}")
    print(f"Modelos AI híbridos: {total_ai_models}/{len(ai_models)}")
    print(f"Tablas de forecasting: {len(forecasting_tables)}")
    print(f"Índices de forecasting: {len(forecasting_indexes)}")
    
    # Calcular porcentaje de completitud
    total_expected = len(ml_models) + len(ai_models)
    total_implemented = total_ml_models + total_ai_models
    completeness = (total_implemented / total_expected) * 100 if total_expected > 0 else 0
    
    print(f"\n🎯 COMPLETITUD: {completeness:.1f}%")
    
    if completeness >= 80:
        print("🎉 ¡Excelente! Arquitectura ML bien implementada")
    elif completeness >= 60:
        print("👍 Buena implementación, algunas mejoras pendientes")
    elif completeness >= 40:
        print("⚠️  Implementación parcial, revisar componentes faltantes")
    else:
        print("❌ Implementación incompleta, requiere trabajo adicional")

if __name__ == "__main__":
    try:
        verify_ml_architecture()
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        sys.exit(1)
