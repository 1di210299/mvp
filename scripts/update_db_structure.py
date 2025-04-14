import sqlite3
import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Ruta a la base de datos SQLite
DB_PATH = "whatsapp_sales.db"

def update_blacklist_table():
    """
    Actualiza la estructura de la tabla blacklist_entries para añadir las columnas
    created_at, updated_at y expiration_date.
    """
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blacklist_entries'")
        if not cursor.fetchone():
            logger.error("La tabla blacklist_entries no existe en la base de datos")
            return False
        
        # Verificar las columnas existentes
        cursor.execute("PRAGMA table_info(blacklist_entries)")
        columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"Columnas actuales en blacklist_entries: {columns}")
        
        # Añadir columnas si no existen
        columns_to_add = []
        if 'created_at' not in columns:
            columns_to_add.append("created_at TIMESTAMP")
        if 'updated_at' not in columns:
            columns_to_add.append("updated_at TIMESTAMP")
        if 'expiration_date' not in columns:
            columns_to_add.append("expiration_date TIMESTAMP")
        
        if not columns_to_add:
            logger.info("Todas las columnas necesarias ya existen")
            return True
        
        # Añadir las columnas faltantes
        for column_def in columns_to_add:
            column_name = column_def.split()[0]
            try:
                logger.info(f"Añadiendo columna: {column_def}")
                cursor.execute(f"ALTER TABLE blacklist_entries ADD COLUMN {column_def}")
                
                # Inicializar con valores por defecto
                if column_name in ['created_at', 'updated_at']:
                    cursor.execute(f"UPDATE blacklist_entries SET {column_name} = CURRENT_TIMESTAMP")
            except sqlite3.OperationalError as e:
                logger.warning(f"Error al añadir columna {column_name}: {str(e)}")
        
        # Guardar cambios
        conn.commit()
        
        # Verificar que se han añadido correctamente
        cursor.execute("PRAGMA table_info(blacklist_entries)")
        new_columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"Columnas actualizadas en blacklist_entries: {new_columns}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error actualizando la estructura de la tabla: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    logger.info("Iniciando actualización de la estructura de la base de datos...")
    
    if not os.path.exists(DB_PATH):
        logger.error(f"La base de datos {DB_PATH} no existe")
        sys.exit(1)
    
    if update_blacklist_table():
        logger.info("¡Actualización completada con éxito!")
    else:
        logger.error("La actualización falló")
        sys.exit(1)