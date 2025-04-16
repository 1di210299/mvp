#!/usr/bin/env python3
"""
Script para desbloquear al cliente específicamente en la tabla de clientes
y verificar todos los posibles formatos del número.
"""
import sys
import os
import sqlite3
from pathlib import Path

# Añadir la raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configurar el número a desbloquear
PHONE_NUMBER = "1di"
DB_PATH = os.path.join(project_root, "whatsapp_sales.db")

def normalize_phone(number):
    """Normalizar el número de teléfono a diferentes formatos posibles"""
    formats = []
    
    # Formato original
    formats.append(number)
    
    # Con prefijo +
    if not number.startswith("+"):
        formats.append("+" + number)
    
    # Con prefijo whatsapp:
    formats.append(f"whatsapp:{number}")
    formats.append(f"whatsapp:+{number}")
    
    return formats

# Conectar a la base de datos SQLite
print(f"Conectando a la base de datos: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Verificar las tablas relevantes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tablas en la base de datos: {tables}")
    
    # Formatos posibles del número de teléfono
    phone_formats = normalize_phone(PHONE_NUMBER)
    print(f"Buscando estos formatos de número: {phone_formats}")
    
    # Comprobar si hay clientes con este número
    print("\n=== BUSCANDO CLIENTES ===")
    for phone_format in phone_formats:
        cursor.execute("""
            SELECT id, phone_number, name, is_blocked, created_at 
            FROM customers 
            WHERE phone_number LIKE ?
        """, (f"%{phone_format}%",))
        
        clients = cursor.fetchall()
        if clients:
            print(f"Encontrados {len(clients)} clientes con formato {phone_format}:")
            for client in clients:
                print(f"ID: {client[0]}, Número: {client[1]}, Nombre: {client[2]}, Bloqueado: {client[3]}, Creado: {client[4]}")
                
                # Desbloquear este cliente
                cursor.execute("""
                    UPDATE customers 
                    SET is_blocked = 0 
                    WHERE id = ?
                """, (client[0],))
                print(f"✅ Cliente ID {client[0]} desbloqueado")
    
    # Comprobar si hay entradas en blacklist
    print("\n=== BUSCANDO EN BLACKLIST ===")
    if "blacklist_entries" in tables:
        for phone_format in phone_formats:
            cursor.execute("""
                SELECT id, phone_number, reason, is_active, created_at 
                FROM blacklist_entries 
                WHERE phone_number LIKE ?
            """, (f"%{phone_format}%",))
            
            entries = cursor.fetchall()
            if entries:
                print(f"Encontradas {len(entries)} entradas en blacklist para {phone_format}:")
                for entry in entries:
                    print(f"ID: {entry[0]}, Número: {entry[1]}, Razón: {entry[2]}, Activo: {entry[3]}, Creado: {entry[4]}")
                    
                    # Desactivar esta entrada
                    cursor.execute("""
                        UPDATE blacklist_entries 
                        SET is_active = 0 
                        WHERE id = ?
                    """, (entry[0],))
                    print(f"✅ Entrada de blacklist ID {entry[0]} desactivada")
    
    # Comprobar conversaciones relevantes
    print("\n=== BUSCANDO CONVERSACIONES ===")
    if "conversations" in tables and "customers" in tables:
        for phone_format in phone_formats:
            cursor.execute("""
                SELECT c.id, c.status, c.created_at, c.customer_id
                FROM conversations c
                JOIN customers cust ON c.customer_id = cust.id
                WHERE cust.phone_number LIKE ?
                ORDER BY c.created_at DESC
                LIMIT 5
            """, (f"%{phone_format}%",))
            
            convs = cursor.fetchall()
            if convs:
                print(f"Encontradas {len(convs)} conversaciones para {phone_format}:")
                for conv in convs:
                    print(f"ID: {conv[0]}, Estado: {conv[1]}, Creado: {conv[2]}, Cliente ID: {conv[3]}")
    
    # Buscar también en la tabla de mensajes
    print("\n=== REVISANDO MENSAJE MÁS RECIENTE ===")
    if "messages" in tables and "customers" in tables and "conversations" in tables:
        for phone_format in phone_formats:
            cursor.execute("""
                SELECT m.id, m.content, m.is_from_customer, m.created_at
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                JOIN customers cust ON c.customer_id = cust.id
                WHERE cust.phone_number LIKE ?
                ORDER BY m.created_at DESC
                LIMIT 1
            """, (f"%{phone_format}%",))
            
            msg = cursor.fetchone()
            if msg:
                print(f"Último mensaje para {phone_format}:")
                print(f"ID: {msg[0]}, Contenido: {msg[1]}, De cliente: {msg[2]}, Fecha: {msg[3]}")
    
    # Guardar cambios
    conn.commit()
    print("\n✅ Todos los cambios guardados en la base de datos")
    
    # Importar directamente del módulo de seguridad para añadir a whitelist
    try:
        from app.security.access_control import add_to_whitelist, WHITELISTED_NUMBERS, BLOCKED_NUMBERS
        
        print("\n=== ACTUALIZANDO LISTAS EN MEMORIA ===")
        
        # Añadir todos los formatos a la whitelist
        for fmt in phone_formats:
            add_to_whitelist(fmt)
            print(f"✅ Formato {fmt} añadido a whitelist")
        
        # Mostrar listas actualizadas
        print(f"Whitelist actual: {list(WHITELISTED_NUMBERS)}")
        print(f"Números bloqueados en memoria: {list(BLOCKED_NUMBERS)}")
        
    except ImportError as e:
        print(f"Error importando módulo de seguridad: {e}")
        print("No se pudieron actualizar las listas en memoria")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("\n✅ PROCESO COMPLETADO")
print("Para que todos los cambios surtan efecto, reinicia la aplicación.")