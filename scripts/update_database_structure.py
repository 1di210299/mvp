#!/usr/bin/env python3
"""
Script para actualizar la estructura de la base de datos.
Añade la columna 'payment_status' a la tabla 'orders'.
"""
import os
import sys
from pathlib import Path

# Añadir la raíz del proyecto al path para poder importar módulos
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Importar los módulos necesarios
from app.db.session import engine, SessionLocal
from app.db.models import Base, PaymentStatus
import sqlalchemy as sa
from sqlalchemy import text

def add_missing_columns():
    """Añade las columnas faltantes en la tabla orders."""
    print("Iniciando actualización de la estructura de la base de datos...")
    
    # Crear una sesión
    db = SessionLocal()
    
    try:
        # Verificar si la columna payment_status existe
        columns_query = "PRAGMA table_info(orders);"
        columns = db.execute(text(columns_query)).fetchall()
        column_names = [col[1] for col in columns]
        
        if 'payment_status' not in column_names:
            print("La columna 'payment_status' no existe en la tabla 'orders'. Añadiendo...")
            
            # Añadir la columna payment_status
            alter_query = "ALTER TABLE orders ADD COLUMN payment_status VARCHAR DEFAULT 'pending';"
            db.execute(text(alter_query))
            
            print("✅ Columna 'payment_status' añadida correctamente.")
        else:
            print("La columna 'payment_status' ya existe. No se requieren cambios.")
        
        # Verificar si hay otras columnas faltantes
        model_columns = {
            'payment_method': "VARCHAR",
            'payment_details': "JSON",
            'payment_date': "TIMESTAMP"
        }
        
        for col_name, col_type in model_columns.items():
            if col_name not in column_names:
                print(f"La columna '{col_name}' no existe. Añadiendo...")
                alter_query = f"ALTER TABLE orders ADD COLUMN {col_name} {col_type};"
                db.execute(text(alter_query))
                print(f"✅ Columna '{col_name}' añadida correctamente.")
        
        # Confirmar cambios
        db.commit()
        print("✅ Base de datos actualizada correctamente.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al actualizar la base de datos: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    add_missing_columns()
    
    # Para recrear todas las tablas conforme al modelo, puedes descomentar esta línea
    # Base.metadata.create_all(bind=engine)
    
    print("Proceso de actualización completado.")