#!/usr/bin/env python3
"""
ANÁLISIS ESPECÍFICO DE LA ESTRUCTURA DE BASE DE DATOS
Revisa únicamente la estructura de la BD y sus datos
"""

import os
import django
from datetime import datetime
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.db import models, connection
from django.apps import apps

def print_header(title):
    """Imprimir encabezado"""
    print("\n" + "="*60)
    print(f"📊 {title}")
    print("="*60)

def print_subheader(title):
    """Imprimir subencabezado"""
    print(f"\n--- {title} ---")

def analyze_database_structure():
    """Analizar estructura completa de la base de datos"""
    print_header("ESTRUCTURA DE LA BASE DE DATOS")
    
    # Información general de la BD
    print_subheader("Información General")
    db_config = django.conf.settings.DATABASES['default']
    print(f"Motor: {db_config['ENGINE']}")
    print(f"Nombre BD: {db_config['NAME']}")
    
    # Obtener todas las tablas
    with connection.cursor() as cursor:
        if 'sqlite' in db_config['ENGINE']:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        else:
            cursor.execute("SHOW TABLES;")
        
        tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Total tablas en BD: {len(tables)}")
    
    # Analizar cada modelo Django
    print_subheader("Modelos Django y sus Tablas")
    
    django_models = []
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            django_models.append(model)
    
    print(f"Total modelos Django: {len(django_models)}")
    
    for model in django_models:
        app_label = model._meta.app_label
        model_name = model.__name__
        table_name = model._meta.db_table
        
        print(f"\n🔹 {app_label}.{model_name}")
        print(f"   Tabla: {table_name}")
        
        # Contar registros
        try:
            count = model.objects.count()
            print(f"   Registros: {count:,}")
        except Exception as e:
            print(f"   Registros: Error - {e}")
        
        # Mostrar campos
        print(f"   Campos:")
        for field in model._meta.fields:
            field_type = field.__class__.__name__
            constraints = []
            
            if field.primary_key:
                constraints.append("PK")
            if field.unique:
                constraints.append("UNIQUE")
            if not field.null:
                constraints.append("NOT NULL")
            if hasattr(field, 'related_model') and field.related_model:
                constraints.append(f"FK→{field.related_model.__name__}")
            
            constraint_str = f" [{', '.join(constraints)}]" if constraints else ""
            print(f"     • {field.name}: {field_type}{constraint_str}")

def analyze_table_relationships():
    """Analizar relaciones entre tablas"""
    print_header("RELACIONES ENTRE TABLAS")
    
    relationships = []
    
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            for field in model._meta.fields:
                if hasattr(field, 'related_model') and field.related_model:
                    relationships.append({
                        'from_model': f"{model._meta.app_label}.{model.__name__}",
                        'from_field': field.name,
                        'to_model': f"{field.related_model._meta.app_label}.{field.related_model.__name__}",
                        'relationship_type': field.__class__.__name__
                    })
    
    print(f"Total relaciones: {len(relationships)}")
    
    # Agrupar por aplicación
    by_app = {}
    for rel in relationships:
        app = rel['from_model'].split('.')[0]
        if app not in by_app:
            by_app[app] = []
        by_app[app].append(rel)
    
    for app, rels in by_app.items():
        print_subheader(f"Relaciones en {app}")
        for rel in rels:
            print(f"  {rel['from_model']}.{rel['from_field']} → {rel['to_model']} ({rel['relationship_type']})")

def analyze_data_distribution():
    """Analizar distribución de datos"""
    print_header("DISTRIBUCIÓN DE DATOS")
    
    total_records = 0
    by_app = {}
    
    for app_config in apps.get_app_configs():
        app_name = app_config.name
        if app_name.startswith('django.'):
            continue
            
        app_total = 0
        models_info = []
        
        for model in app_config.get_models():
            try:
                count = model.objects.count()
                total_records += count
                app_total += count
                models_info.append((model.__name__, count))
            except:
                models_info.append((model.__name__, 0))
        
        by_app[app_name] = {
            'total': app_total,
            'models': models_info
        }
    
    print(f"🎯 TOTAL REGISTROS EN BD: {total_records:,}")
    
    for app_name, info in by_app.items():
        print_subheader(f"{app_name} ({info['total']:,} registros)")
        for model_name, count in sorted(info['models'], key=lambda x: x[1], reverse=True):
            percentage = (count / max(total_records, 1)) * 100
            print(f"  • {model_name}: {count:,} ({percentage:.1f}%)")

def analyze_indexes_and_constraints():
    """Analizar índices y restricciones"""
    print_header("ÍNDICES Y RESTRICCIONES")
    
    # Obtener información de índices (solo para SQLite por simplicidad)
    db_config = django.conf.settings.DATABASES['default']
    
    if 'sqlite' in db_config['ENGINE']:
        with connection.cursor() as cursor:
            # Obtener información de índices
            cursor.execute("""
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type = 'index' 
                AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name
            """)
            
            indexes = cursor.fetchall()
            
            print_subheader(f"Índices ({len(indexes)} encontrados)")
            current_table = None
            for index_name, table_name, sql in indexes:
                if table_name != current_table:
                    print(f"\n📋 Tabla: {table_name}")
                    current_table = table_name
                print(f"  • {index_name}")
    else:
        print("⚠️  Análisis de índices solo disponible para SQLite")

def analyze_database_size():
    """Analizar tamaño de la base de datos"""
    print_header("TAMAÑO DE LA BASE DE DATOS")
    
    db_config = django.conf.settings.DATABASES['default']
    db_path = Path(db_config['NAME'])
    
    if db_path.exists():
        size_bytes = db_path.stat().st_size
        size_mb = size_bytes / 1024 / 1024
        
        print(f"📁 Archivo de BD: {db_path}")
        print(f"💾 Tamaño: {size_mb:.2f} MB ({size_bytes:,} bytes)")
        
        # Estimar tamaño por tabla (aproximado)
        total_records = 0
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                try:
                    count = model.objects.count()
                    total_records += count
                except:
                    pass
        
        if total_records > 0:
            avg_record_size = size_bytes / total_records
            print(f"📊 Tamaño promedio por registro: {avg_record_size:.1f} bytes")
    else:
        print("❌ No se pudo encontrar el archivo de base de datos")

def check_database_integrity():
    """Verificar integridad de la base de datos"""
    print_header("VERIFICACIÓN DE INTEGRIDAD")
    
    issues = []
    warnings = []
    
    # Verificar relaciones rotas
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            for field in model._meta.fields:
                if hasattr(field, 'related_model') and field.related_model:
                    try:
                        # Verificar registros huérfanos
                        orphan_count = model.objects.filter(
                            **{f"{field.name}__isnull": True}
                        ).count()
                        
                        if orphan_count > 0 and not field.null:
                            issues.append(f"❌ {model.__name__}.{field.name}: {orphan_count} registros con FK nula")
                    except:
                        pass
    
    # Verificar duplicados en campos únicos
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            for field in model._meta.fields:
                if field.unique and not field.primary_key:
                    try:
                        from django.db.models import Count
                        duplicates = model.objects.values(field.name).annotate(
                            count=Count(field.name)
                        ).filter(count__gt=1)
                        
                        if duplicates.exists():
                            issues.append(f"❌ {model.__name__}.{field.name}: Valores duplicados en campo único")
                    except:
                        pass
    
    if issues:
        print("🚨 PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"  {issue}")
    
    if warnings:
        print("\n⚠️  ADVERTENCIAS:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not issues and not warnings:
        print("✅ No se encontraron problemas de integridad")

def main():
    """Función principal"""
    import sys
    from io import StringIO
    
    # Crear archivo de salida
    output_file = f"database_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Capturar toda la salida
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        print("🗄️  ANÁLISIS DE ESTRUCTURA DE BASE DE DATOS")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📍 Proyecto: DataLens MVP")
        print("="*80)
        
        analyze_database_structure()
        analyze_table_relationships()
        analyze_data_distribution()
        analyze_indexes_and_constraints()
        analyze_database_size()
        check_database_integrity()
        
        print("\n" + "🎉"*60)
        print("✅ ANÁLISIS DE BD COMPLETADO")
        print("🎉"*60)
        print(f"\n📄 Reporte guardado en: {output_file}")
        
        # Obtener contenido capturado
        output_content = sys.stdout.getvalue()
        
        # Restaurar stdout
        sys.stdout = old_stdout
        
        # Guardar en archivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_content)
        
        # Mostrar en consola también
        print("🗄️  ANÁLISIS DE ESTRUCTURA DE BASE DE DATOS")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📍 Proyecto: DataLens MVP")
        print(f"📄 Reporte guardado en: {output_file}")
        print("✅ Análisis completado exitosamente")
        
    except Exception as e:
        # Restaurar stdout en caso de error
        sys.stdout = old_stdout
        print(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
