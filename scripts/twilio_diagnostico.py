#!/usr/bin/env python3
"""
Script para diagnosticar y resolver problemas con el Sandbox de Twilio WhatsApp.
Este script verifica la configuración de Twilio, los participantes del Sandbox,
y proporciona información para resolver problemas de bloqueo.
"""
import os
import sys
from pathlib import Path

# Añadir la raíz del proyecto al path para poder importar módulos
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    # Importar configuración y cliente de Twilio
    from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
    from twilio.rest import Client
    
    # Inicializar cliente de Twilio
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    # Obtener el número de teléfono de WhatsApp de Twilio (el de la sandbox)
    TWILIO_WHATSAPP = "+14155238886"  # Número estándar del sandbox de Twilio
    
    # Número específico a desbloquear
    TARGET_NUMBER = "+51955743403"  # El número real del usuario
    
    def check_twilio_settings():
        """Verifica la configuración de Twilio"""
        print("\n=== VERIFICANDO CONFIGURACIÓN DE TWILIO ===")
        
        try:
            # Verificar cuenta
            account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
            print(f"✅ Cuenta Twilio: {account.friendly_name}")
            print(f"✅ Estado de la cuenta: {account.status}")
            
            # Verificar números de teléfono
            numbers = client.incoming_phone_numbers.list()
            if numbers:
                print(f"✅ Números disponibles en la cuenta:")
                for number in numbers:
                    print(f"   • {number.phone_number} ({number.friendly_name})")
            else:
                print("⚠️ No se encontraron números de teléfono en la cuenta")
                
            return True
        except Exception as e:
            print(f"❌ Error al verificar configuración: {str(e)}")
            return False
    
    def check_whatsapp_sandbox():
        """Verifica la configuración del Sandbox de WhatsApp"""
        print("\n=== VERIFICANDO SANDBOX DE WHATSAPP ===")
        
        try:
            # Intentar obtener los participantes del Sandbox
            # Nota: Esta API puede variar según la versión de Twilio
            participants = []
            
            try:
                # Método 1: A través de la API de Conversations (versión más reciente)
                conversations = client.conversations.v1.conversations.list(limit=20)
                for conv in conversations:
                    try:
                        participants_list = client.conversations.v1.conversations(conv.sid).participants.list()
                        for participant in participants_list:
                            if "whatsapp:" in participant.identity:
                                participants.append(participant.identity)
                    except:
                        pass
            except:
                pass
                
            if not participants:
                # Método 2: A través de mensajes recientes
                try:
                    messages = client.messages.list(limit=100)
                    for msg in messages:
                        if msg.to and "whatsapp:" in msg.to:
                            if msg.to not in participants:
                                participants.append(msg.to)
                        if msg.from_ and "whatsapp:" in msg.from_:
                            if msg.from_ not in participants:
                                participants.append(msg.from_)
                except:
                    pass
            
            if participants:
                print(f"✅ Participantes encontrados en el Sandbox:")
                for participant in participants:
                    print(f"   • {participant}")
            else:
                print("⚠️ No se encontraron participantes en el Sandbox")
                
            # Verificar configuración del Sandbox
            print("\n✅ Instrucciones para unirse al Sandbox:")
            print(f"   1. Usa WhatsApp y envía un mensaje a {TWILIO_WHATSAPP}")
            print(f"   2. El mensaje debe ser: join move-weather")
            print(f"   3. Deberías recibir un mensaje de confirmación")
            
            return participants
        except Exception as e:
            print(f"❌ Error al verificar Sandbox: {str(e)}")
            return []
    
    def check_specific_number(phone_number):
        """Verifica el estado de un número específico"""
        print(f"\n=== VERIFICANDO NÚMERO: {phone_number} ===")
        
        # Normalizar formato
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number
            
        # Formato para WhatsApp
        whatsapp_number = f"whatsapp:{phone_number}"
        
        try:
            # Verificar mensajes recientes a este número
            messages_to = client.messages.list(to=whatsapp_number, limit=5)
            print(f"✅ Mensajes enviados a este número (últimos 5):")
            if messages_to:
                for msg in messages_to:
                    print(f"   • {msg.date_sent} - Estado: {msg.status}")
                    print(f"     Contenido: {msg.body[:50]}..." if len(msg.body) > 50 else f"     Contenido: {msg.body}")
            else:
                print("   • No se encontraron mensajes enviados a este número")
                
            # Verificar mensajes recientes desde este número
            messages_from = client.messages.list(from_=whatsapp_number, limit=5)
            print(f"\n✅ Mensajes recibidos de este número (últimos 5):")
            if messages_from:
                for msg in messages_from:
                    print(f"   • {msg.date_sent} - Estado: {msg.status}")
                    print(f"     Contenido: {msg.body[:50]}..." if len(msg.body) > 50 else f"     Contenido: {msg.body}")
            else:
                print("   • No se encontraron mensajes recibidos de este número")
                
            # Verificar si el número está registrado en el Sandbox
            participants = check_whatsapp_sandbox()
            if whatsapp_number in participants:
                print(f"\n✅ El número {whatsapp_number} está registrado en el Sandbox")
            else:
                print(f"\n⚠️ El número {whatsapp_number} NO está registrado en el Sandbox")
                print("   Esto puede ser la causa del bloqueo de mensajes.")
                print("   Para solucionar esto:")
                print(f"   1. Desde el WhatsApp con el número {phone_number}, envía un mensaje a {TWILIO_WHATSAPP}")
                print("   2. El mensaje debe ser exactamente: join move-weather")
            
            return True
        except Exception as e:
            print(f"❌ Error al verificar número: {str(e)}")
            return False
            
    def send_test_message(phone_number, message="¡Hola! Este es un mensaje de prueba para verificar la conexión. Si lo recibes, por favor responde."):
        """Envía un mensaje de prueba a un número"""
        print(f"\n=== ENVIANDO MENSAJE DE PRUEBA A: {phone_number} ===")
        
        # Normalizar formato
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number
            
        # Formato para WhatsApp
        whatsapp_number = f"whatsapp:{phone_number}"
        
        try:
            # Obtener el número de WhatsApp de Twilio
            whatsapp_sender = f"whatsapp:{TWILIO_WHATSAPP}"
            
            # Enviar mensaje
            message = client.messages.create(
                from_=whatsapp_sender,
                body=message,
                to=whatsapp_number
            )
            
            print(f"✅ Mensaje enviado con SID: {message.sid}")
            print(f"✅ Estado: {message.status}")
            
            return True
        except Exception as e:
            print(f"❌ Error al enviar mensaje: {str(e)}")
            return False
    
    def unblock_specific_number(phone_number):
        """
        Intenta desbloquear completamente un número específico en todas las capas posibles
        """
        print(f"\n=== DESBLOQUEANDO NÚMERO: {phone_number} ===")
        
        # Normalizar formato
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number
            
        # Formato para WhatsApp
        whatsapp_number = f"whatsapp:{phone_number}"
        
        try:
            print("1. Intentando desbloquear en la aplicación...")
            try:
                from app.security.access_control import add_to_whitelist, WHITELISTED_NUMBERS, BLOCKED_NUMBERS
                
                # Añadir a whitelist con diferentes formatos
                for fmt in [phone_number, whatsapp_number, phone_number.lstrip("+")]:
                    add_to_whitelist(fmt)
                    print(f"   ✅ Formato {fmt} añadido a whitelist")
                
                # Eliminar de la lista de bloqueados si existe
                for fmt in [phone_number, whatsapp_number, phone_number.lstrip("+")]:
                    if fmt in BLOCKED_NUMBERS:
                        BLOCKED_NUMBERS.remove(fmt)
                        print(f"   ✅ Formato {fmt} eliminado de la lista de bloqueados")
                
                print(f"   ℹ️ Whitelist actual: {list(WHITELISTED_NUMBERS)}")
                print(f"   ℹ️ Lista de bloqueados actual: {list(BLOCKED_NUMBERS)}")
                
            except ImportError:
                print("   ⚠️ No se pudo acceder a los módulos de control de acceso")
            
            print("\n2. Intentando desbloquear en la base de datos...")
            try:
                from app.db.session import SessionLocal
                from sqlalchemy import text
                
                # Conectar a la base de datos
                db = SessionLocal()
                
                # Formatos posibles para buscar en la base de datos
                formats = [
                    phone_number, 
                    whatsapp_number, 
                    phone_number.lstrip("+"),
                    "%" + phone_number + "%",
                    "%" + whatsapp_number + "%"
                ]
                
                try:
                    # Verificar qué tablas existen
                    tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
                    table_names = [t[0] for t in tables]
                    print(f"   ℹ️ Tablas en la base de datos: {table_names}")
                    
                    # Intentar desbloquear en las tablas relevantes
                    if 'blacklist_entries' in table_names:
                        for fmt in formats:
                            db.execute(
                                text("UPDATE blacklist_entries SET is_active = 0 WHERE phone_number LIKE :phone"),
                                {"phone": fmt}
                            )
                        print("   ✅ Entradas en blacklist_entries desactivadas")
                        
                    if 'customers' in table_names:
                        for fmt in formats:
                            db.execute(
                                text("UPDATE customers SET is_blocked = 0 WHERE phone_number LIKE :phone"),
                                {"phone": fmt}
                            )
                        print("   ✅ Cliente desbloqueado en tabla customers")
                        
                    # Buscar información del cliente para diagnóstico
                    if 'customers' in table_names:
                        customer = db.execute(
                            text("SELECT id, phone_number, is_blocked FROM customers WHERE phone_number LIKE :phone"),
                            {"phone": "%" + phone_number + "%"}
                        ).fetchone()
                        
                        if customer:
                            print(f"   ℹ️ Cliente encontrado: ID={customer[0]}, Número={customer[1]}, Bloqueado={customer[2]}")
                        else:
                            print(f"   ⚠️ No se encontró cliente con este número")
                            # Crear cliente si no existe
                            try:
                                from app.db.repositories import create_customer
                                new_customer = create_customer(db, whatsapp_number)
                                print(f"   ✅ Nuevo cliente creado con ID {new_customer.id}")
                            except Exception as e:
                                print(f"   ❌ No se pudo crear cliente: {str(e)}")
                    
                    # Guardar cambios
                    db.commit()
                    print("   ✅ Cambios guardados en la base de datos")
                    
                except Exception as e:
                    print(f"   ❌ Error en operaciones de base de datos: {str(e)}")
                    db.rollback()
                finally:
                    db.close()
                    
            except ImportError:
                print("   ⚠️ No se pudo acceder a los módulos de base de datos")
            
            print("\n3. Enviando mensaje de prueba para verificar desbloqueo...")
            send_test_message(phone_number, "✅ PRUEBA DE DESBLOQUEO: Si recibes este mensaje, el número ha sido desbloqueado correctamente. Por favor, responde para confirmar.")
            
            print("\n✅ Proceso de desbloqueo completado")
            print("ℹ️ Para que todos los cambios surtan efecto, reinicia la aplicación.")
            
            return True
        except Exception as e:
            print(f"❌ Error general en desbloqueo: {str(e)}")
            return False
            
    def main():
        print("=" * 70)
        print("🔍 HERRAMIENTA DE DIAGNÓSTICO PARA TWILIO WHATSAPP SANDBOX")
        print("=" * 70)
        
        # Verificar configuración de Twilio
        check_twilio_settings()
        
        # Verificar Sandbox de WhatsApp
        check_whatsapp_sandbox()
        
        # Solicitar número a verificar
        if len(sys.argv) > 1:
            phone_number = sys.argv[1]
        else:
            phone_number = input("\nIngresa el número a verificar (ej: +51955743403): ")
        
        # Verificar el número específico
        check_specific_number(phone_number)
        
        # Preguntar si desea desbloquear el número
        unblock = input("\n¿Deseas intentar desbloquear este número en todas las capas? (s/n): ")
        if unblock.lower() in ('s', 'si', 'sí', 'y', 'yes'):
            unblock_specific_number(phone_number)
        
        # Preguntar si desea enviar un mensaje de prueba
        send_test = input("\n¿Deseas enviar un mensaje de prueba a este número? (s/n): ")
        if send_test.lower() in ('s', 'si', 'sí', 'y', 'yes'):
            custom_message = input("Ingresa un mensaje personalizado (o presiona Enter para usar el predeterminado): ")
            if custom_message:
                send_test_message(phone_number, custom_message)
            else:
                send_test_message(phone_number)
        
        print("\n=" * 70)
        print("✅ DIAGNÓSTICO COMPLETADO")
        print("=" * 70)
        print("\nSi aún tienes problemas, asegúrate de que:")
        print("1. El número esté registrado en el Sandbox de WhatsApp")
        print("2. La configuración del webhook esté correcta")
        print("3. Tu servidor esté en línea y accesible desde Internet")
        print("\nPara más ayuda, consulta la documentación de Twilio WhatsApp:")
        print("https://www.twilio.com/docs/whatsapp/sandbox")

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Error importando módulos necesarios: {str(e)}")
    print("Asegúrate de tener instalado el módulo twilio: pip install twilio")
    print("Y de estar ejecutando este script desde la raíz del proyecto")
    sys.exit(1)
except Exception as e:
    print(f"Error inesperado: {str(e)}")
    sys.exit(1)