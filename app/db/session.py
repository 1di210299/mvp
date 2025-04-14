from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL

# Crear el motor de base de datos
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa que usarán los modelos
Base = declarative_base()

# Función para obtener la conexión a BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()