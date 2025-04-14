import logging
import os
import sys
from pathlib import Path

# Añadir directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.exc import SQLAlchemyError
from app.db.models import Base, Product, BlacklistEntry
from app.db.session import engine, SessionLocal
from app.security.blacklist import sync_with_csv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_tables():
    """Crea todas las tablas en la base de datos."""
    try:
        logger.info("Creando tablas en la base de datos...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas correctamente.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error al crear tablas: {str(e)}")
        return False

def insert_demo_data():
    """Inserta datos de ejemplo para desarrollo."""
    try:
        db = SessionLocal()
        
        # Verificar si ya hay productos
        existing_products = db.query(Product).count()
        if existing_products > 0:
            logger.info(f"Ya existen {existing_products} productos en la base de datos.")
            db.close()
            return True
        
        # Crear productos de ejemplo
        logger.info("Insertando productos de ejemplo...")
        products = [
            Product(
                name="Agua Mineral",
                code="A01",
                description="Botella de agua mineral de 500ml",
                price=2.50,
                inventory=100,
                is_active=True
            ),
            Product(
                name="Gaseosa Cola",
                code="B01",
                description="Gaseosa cola de 500ml",
                price=3.50,
                inventory=80,
                is_active=True
            ),
            Product(
                name="Sandwich de Pollo",
                code="C01",
                description="Sandwich de pollo con lechuga y tomate",
                price=8.90,
                inventory=50,
                is_active=True
            ),
            Product(
                name="Chocolate",
                code="D01",
                description="Barra de chocolate con leche",
                price=4.20,
                inventory=120,
                is_active=True
            ),
            Product(
                name="Papas Fritas",
                code="E01",
                description="Bolsa de papas fritas sabor clásico",
                price=5.50,
                inventory=70,
                is_active=True
            )
        ]
        
        db.add_all(products)
        db.commit()
        logger.info(f"Se insertaron {len(products)} productos de ejemplo.")
        
        # Crear lista negra de ejemplo (opcional)
        logger.info("Sincronizando lista negra desde CSV...")
        added_count = sync_with_csv(db)
        logger.info(f"Se añadieron {added_count} números a la lista negra.")
        
        db.close()
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Error al insertar datos de ejemplo: {str(e)}")
        return False
    finally:
        try:
            db.close()
        except:
            pass

if __name__ == "__main__":
    # Verificar si queremos forzar la recreación de tablas
    force_reset = len(sys.argv) > 1 and sys.argv[1] == "--reset"
    
    if force_reset:
        try:
            logger.warning("Eliminando todas las tablas existentes...")
            Base.metadata.drop_all(bind=engine)
            logger.info("Tablas eliminadas correctamente.")
        except SQLAlchemyError as e:
            logger.error(f"Error al eliminar tablas: {str(e)}")
    
    # Crear tablas
    if create_tables():
        # Insertar datos de ejemplo
        insert_demo_data()
        
        logger.info("Configuración completada correctamente.")
    else:
        logger.error("La configuración falló debido a errores.")
        sys.exit(1)