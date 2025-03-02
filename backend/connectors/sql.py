import os
import sqlite3
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env (útil en desarrollo)
load_dotenv()

# Importaciones condicionales para MySQL y PostgreSQL
try:
    import MySQLdb
except ImportError:
    MySQLdb = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None

def test_sql_connection(connection_string, username=None, password=None, query=None):
    """
    Prueba una conexión SQL y devuelve metadatos sobre los datos.
    
    Parámetros:
      connection_string (str): Cadena de conexión.
          - Para MySQL: "mysql://host/database"
          - Para PostgreSQL: "postgresql://host/database"
          - Para SQLite: Ruta al archivo (e.g., "test.db" o ":memory:")
      username (str, opcional): Nombre de usuario. Si no se proporciona, se intenta leer desde
          las variables de entorno (MYSQL_USER o PG_USER según corresponda).
      password (str, opcional): Contraseña. Si no se proporciona, se intenta leer desde
          las variables de entorno (MYSQL_PASS o PG_PASS según corresponda).
      query (str, opcional): Consulta SQL para ejecutar. Si no se proporciona, se ejecuta "SELECT 1".
    
    Retorna:
      dict: Diccionario con el estado de la conexión, columnas, datos de muestra y cantidad de columnas.
    
    Lanza:
      Exception: Con mensajes descriptivos en caso de error en la conexión o en la ejecución.
    """
    # Si no se proporciona username o password, se leen de las variables de entorno
    if username is None:
        if 'mysql://' in connection_string:
            username = os.environ.get("MYSQL_USER")
        elif 'postgresql://' in connection_string:
            username = os.environ.get("PG_USER")
    
    if password is None:
        if 'mysql://' in connection_string:
            password = os.environ.get("MYSQL_PASS")
        elif 'postgresql://' in connection_string:
            password = os.environ.get("PG_PASS")
    
    # Conexión a MySQL
    if 'mysql://' in connection_string:
        if MySQLdb is None:
            raise ImportError("Para conectar a MySQL, necesitas instalar el paquete 'mysqlclient'")
        
        host = connection_string.replace('mysql://', '').split('/')[0]
        database = connection_string.split('/')[-1] if '/' in connection_string else ''
        
        conn = MySQLdb.connect(
            host=host,
            user=username,
            passwd=password,
            db=database
        )
        cursor = conn.cursor()
    
    # Conexión a PostgreSQL
    elif 'postgresql://' in connection_string:
        if psycopg2 is None:
            raise ImportError("Para conectar a PostgreSQL, necesitas instalar el paquete 'psycopg2-binary'")
        
        host = connection_string.replace('postgresql://', '').split('/')[0]
        database = connection_string.split('/')[-1] if '/' in connection_string else ''
        
        conn = psycopg2.connect(
            host=host,
            user=username,
            password=password,
            dbname=database
        )
        cursor = conn.cursor()
    
    # Conexión a SQLite (por defecto)
    else:
        # Si es una ruta relativa y el archivo no existe, se intenta crear el archivo vacío
        if connection_string != ':memory:' and not os.path.exists(connection_string) and not connection_string.startswith('/'):
            try:
                open(connection_string, 'a').close()
            except Exception as e:
                raise Exception(f"No se pudo crear la base de datos SQLite: {str(e)}")
                
        conn = sqlite3.connect(connection_string)
        cursor = conn.cursor()
    
    # Ejecutar consulta de prueba
    if not query:
        cursor.execute("SELECT 1")
        metadata = {"connected": True, "columns": [], "sample_data": []}
    else:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(5)  # Obtenemos hasta 5 filas de muestra
        metadata = {
            "connected": True,
            "columns": columns,
            "sample_data": rows,
            "column_count": len(columns)
        }
    
    cursor.close()
    conn.close()
    return metadata
