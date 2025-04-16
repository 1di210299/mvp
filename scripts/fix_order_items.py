#!/usr/bin/env python3
"""
Script para actualizar la estructura de la base de datos.
Añade la columna 'subtotal' a la tabla 'order_items' si falta o la modifica.
"""
import os
import sys
from pathlib import Path

# Añadir la raíz del proyecto al path para poder importar módulos
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Importar los módulos necesarios
from app.db.session import engine, SessionLocal
from app.db.models import Base
import sqlalchemy as sa
from sqlalchemy import text

def update_order_items_table():
    """Actualiza la estructura de la tabla order_items."""
    print("Iniciando actualización de la tabla order_items...")
    
    # Crear una sesión
    db = SessionLocal()
    
    try:
        # Verificar si la columna subtotal existe
        columns_query = "PRAGMA table_info(order_items);"
        columns = db.execute(text(columns_query)).fetchall()
        column_names = [col[1] for col in columns]
        
        if 'subtotal' not in column_names:
            print("La columna 'subtotal' no existe en la tabla 'order_items'. Añadiendo...")
            
            # Añadir la columna subtotal
            alter_query = "ALTER TABLE order_items ADD COLUMN subtotal FLOAT;"
            db.execute(text(alter_query))
            
            print("✅ Columna 'subtotal' añadida correctamente.")
            
            # Actualizar valores existentes para calcular subtotal
            update_query = """
            UPDATE order_items 
            SET subtotal = quantity * unit_price 
            WHERE subtotal IS NULL;
            """
            db.execute(text(update_query))
            print("✅ Valores de subtotal actualizados correctamente.")
        else:
            # Verificar si hay registros con subtotal NULL
            null_check = "SELECT COUNT(*) FROM order_items WHERE subtotal IS NULL;"
            null_count = db.execute(text(null_check)).fetchone()[0]
            
            if null_count > 0:
                print(f"Encontrados {null_count} registros con subtotal NULL. Actualizando...")
                update_query = """
                UPDATE order_items 
                SET subtotal = quantity * unit_price 
                WHERE subtotal IS NULL;
                """
                db.execute(text(update_query))
                print("✅ Valores de subtotal actualizados correctamente.")
            else:
                print("La columna 'subtotal' ya existe y no hay valores NULL. No se requieren cambios.")
        
        # Confirmar cambios
        db.commit()
        print("✅ Tabla order_items actualizada correctamente.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al actualizar la tabla order_items: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    update_order_items_table()
    print("Proceso de actualización completado.")