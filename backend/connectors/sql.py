import MySQLdb
import psycopg2
import sqlite3

def test_sql_connection(connection_string, username, password, query=None):
    """
    Prueba una conexión SQL y devuelve metadatos sobre los datos.
    """
    # Analizamos la cadena de conexión
    if 'mysql://' in connection_string:
        # MySQL
        host = connection_string.replace('mysql://', '').split('/')[0]
        database = connection_string.split('/')[-1] if '/' in connection_string else ''
        
        conn = MySQLdb.connect(
            host=host,
            user=username,
            passwd=password,
            db=database
        )
        cursor = conn.cursor()
        
    elif 'postgresql://' in connection_string:
        # PostgreSQL
        host = connection_string.replace('postgresql://', '').split('/')[0]
        database = connection_string.split('/')[-1] if '/' in connection_string else ''
        
        conn = psycopg2.connect(
            host=host,
            user=username,
            password=password,
            dbname=database
        )
        cursor = conn.cursor()
    
    else:
        # SQLite por defecto
        conn = sqlite3.connect(connection_string)
        cursor = conn.cursor()
    
    # Probamos la conexión con una consulta simple
    if not query:
        cursor.execute("SELECT 1")
        metadata = {"connected": True, "columns": [], "sample_data": []}
    else:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchmany(5)  # Obtenemos 5 filas como muestra
        
        metadata = {
            "connected": True,
            "columns": columns,
            "sample_data": rows,
            "column_count": len(columns)
        }
    
    cursor.close()
    conn.close()
    
    return metadata