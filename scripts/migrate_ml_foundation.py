#!/usr/bin/env python3
"""
MIGRATION MANAGER - Foundation Architecture
==========================================

Script para crear y aplicar migraciones del sistema ML Foundation
Maneja:
- Nuevos modelos ML Core (MLModelVersion, MLMetric, etc.)
- Campos adicionales en Customer Intelligence
- Campos adicionales en Financial Forecasting  
- Índices optimizados para performance

Uso:
python migrate_ml_foundation.py [--dry-run] [--create-only] [--apply-only]
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import call_command
from django.db import connection
import subprocess

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

def print_header(text):
    print(f"\n{'='*60}")
    print(f"📋 {text}")
    print('='*60)

def print_step(step, text):
    print(f"\n{step}. {text}")

def run_command(cmd, description):
    """Ejecutar comando y manejar errores"""
    print(f"   🔧 {description}")
    print(f"   $ {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {description} - Exitoso")
            if result.stdout:
                print(f"   📄 Output: {result.stdout.strip()}")
        else:
            print(f"   ❌ {description} - Error")
            print(f"   📄 Error: {result.stderr.strip()}")
            return False
        return True
    except Exception as e:
        print(f"   ❌ {description} - Exception: {str(e)}")
        return False

def check_database_status():
    """Verificar estado actual de la base de datos"""
    print_step("1", "Verificando estado de la base de datos")
    
    try:
        # Verificar tablas existentes (compatible con SQLite y PostgreSQL)
        with connection.cursor() as cursor:
            # Para SQLite
            if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name LIKE 'forecasting_%'
                    ORDER BY name;
                """)
            else:
                # Para PostgreSQL
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'forecasting_%'
                    ORDER BY table_name;
                """)
            
            existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"   📊 Tablas forecasting existentes: {len(existing_tables)}")
        for table in existing_tables:
            print(f"      - {table}")
        
        # Verificar migraciones pendientes
        print("\n   🔍 Verificando migraciones pendientes...")
        run_command("python manage.py showmigrations forecasting", "Mostrar estado migraciones")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error verificando BD: {str(e)}")
        return False

def create_migrations():
    """Crear nuevas migraciones"""
    print_step("2", "Creando migraciones para nuevos modelos")
    
    # Crear migración para nuevos modelos ML Core
    success = run_command(
        "python manage.py makemigrations forecasting --name ml_foundation_architecture",
        "Crear migración ML Foundation"
    )
    
    if not success:
        print("   ⚠️ No se pudieron crear las migraciones. Verifica errores de modelo.")
        return False
    
    return True

def apply_migrations(dry_run=False):
    """Aplicar migraciones"""
    if dry_run:
        print_step("3", "Simulando migraciones (usando --plan)")
        # Django no tiene --dry-run, pero podemos usar --plan para ver qué se aplicaría
        success = run_command(
            "python manage.py migrate forecasting --plan",
            "Ver plan de migraciones forecasting"
        )
    else:
        print_step("3", "Aplicando migraciones")
        success = run_command(
            "python manage.py migrate forecasting",
            "Aplicar migraciones forecasting"
        )
    
    if not success:
        return False
    
    if not dry_run:
        print("   ✅ Migraciones aplicadas exitosamente")
    else:
        print("   ✅ Plan de migraciones mostrado exitosamente")
    
    return True

def create_indexes():
    """Crear índices optimizados manualmente si es necesario"""
    print_step("4", "Verificando índices optimizados")
    
    # Índices adaptados para SQLite (sin CONCURRENTLY)
    if 'sqlite' in settings.DATABASES['default']['ENGINE']:
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_ml_model_version_active ON forecasting_mlmodelversion(is_active, deployment_status);",
            "CREATE INDEX IF NOT EXISTS idx_ml_metrics_type_date ON forecasting_mlmetric(metric_type, calculation_date);",
            "CREATE INDEX IF NOT EXISTS idx_customer_clv_score ON forecasting_customerlifetimevalue(predicted_clv, customer_segment);",
            "CREATE INDEX IF NOT EXISTS idx_churn_risk_level ON forecasting_churnprediction(risk_level, churn_probability);",
        ]
    else:
        # PostgreSQL con CONCURRENTLY
        indexes_sql = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ml_model_version_active ON forecasting_mlmodelversion(is_active, deployment_status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ml_metrics_type_date ON forecasting_mlmetric(metric_type, calculation_date);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customer_clv_score ON forecasting_customerlifetimevalue(predicted_clv, customer_segment);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_churn_risk_level ON forecasting_churnprediction(risk_level, churn_probability);",
        ]
    
    try:
        with connection.cursor() as cursor:
            for sql in indexes_sql:
                print(f"   🔧 Creando índice: {sql[:50]}...")
                try:
                    cursor.execute(sql)
                    print(f"   ✅ Índice creado")
                except Exception as e:
                    print(f"   ⚠️ Índice ya existe o error: {str(e)}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error creando índices: {str(e)}")
        return False

def validate_models():
    """Validar que los modelos funcionen correctamente"""
    print_step("5", "Validando modelos ML Foundation")
    
    try:
        # Importar modelos para verificar
        from forecasting.models import (
            MLModelVersion, MLMetric, MLExperiment, 
            MLModelRegistry, MLDatasetVersion,
            CustomerLifetimeValue, ChurnPrediction,
            FinancialForecastModel
        )
        
        print("   ✅ Todos los modelos ML Core importados correctamente")
        
        # Verificar que las tablas existen
        models_to_check = [
            (MLModelVersion, 'MLModelVersion'),
            (MLMetric, 'MLMetric'),
            (MLExperiment, 'MLExperiment'),
            (CustomerLifetimeValue, 'CustomerLifetimeValue'),
            (ChurnPrediction, 'ChurnPrediction'),
            (FinancialForecastModel, 'FinancialForecastModel'),
        ]
        
        for model_class, model_name in models_to_check:
            try:
                count = model_class.objects.count()
                print(f"   ✅ {model_name}: {count} registros")
            except Exception as e:
                print(f"   ❌ {model_name}: Error - {str(e)}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Error importando modelos: {str(e)}")
        return False

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migration Manager for ML Foundation')
    parser.add_argument('--dry-run', action='store_true', help='Simular migraciones sin aplicar')
    parser.add_argument('--create-only', action='store_true', help='Solo crear migraciones')
    parser.add_argument('--apply-only', action='store_true', help='Solo aplicar migraciones existentes')
    
    args = parser.parse_args()
    
    print_header("MIGRATION MANAGER - ML FOUNDATION ARCHITECTURE")
    print("🚀 Iniciando proceso de migración para sistema ML escalable")
    
    # Verificar estado actual
    if not check_database_status():
        print("\n❌ Error verificando estado de BD. Abortando.")
        return False
    
    success = True
    
    # Crear migraciones (si no es apply-only)
    if not args.apply_only:
        success = create_migrations()
        if not success:
            print("\n❌ Error creando migraciones. Abortando.")
            return False
    
    # Salir si solo queremos crear
    if args.create_only:
        print("\n✅ Migraciones creadas. Use --apply-only para aplicar.")
        return True
    
    # Aplicar migraciones
    success = apply_migrations(dry_run=args.dry_run)
    if not success:
        print("\n❌ Error aplicando migraciones. Abortando.")
        return False
    
    # Si es dry-run, salir aquí
    if args.dry_run:
        print("\n✅ Simulación completada. Use sin --dry-run para aplicar realmente.")
        return True
    
    # Crear índices optimizados
    success = create_indexes()
    if not success:
        print("\n⚠️ Error creando índices (no crítico).")
    
    # Validar modelos
    success = validate_models()
    if not success:
        print("\n❌ Error validando modelos.")
        return False
    
    print_header("MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("🎉 Sistema ML Foundation Architecture implementado")
    print("\n📋 Próximos pasos:")
    print("   1. Ejecutar test_ml_comprehensive.py para verificar funcionalidad")
    print("   2. Corregir training_service.py para usar campo 'model' vs 'forecast_model'")
    print("   3. Corregir Prophet timezone issues")
    print("   4. Implementar monitoring y alertas")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
