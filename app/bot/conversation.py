import logging
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db import repositories
from app.db.models import Customer, Conversation, ConversationStatus, OrderStatus
from app.services import openai_service
from app.bot import responses

# Configurar logging
logger = logging.getLogger(__name__)

# Estados de conversación para el flujo básico
class ConversationState:
    INITIAL = "initial"
    GREETING = "greeting"
    CONSENT = "consent"
    REGISTRATION = "registration"
    MENU = "menu"
    PRODUCT_SELECTION = "product_selection"
    CART = "cart"
    CHECKOUT = "checkout"
    PAYMENT = "payment"
    COMPLETED = "completed"
    BLOCKED = "blocked"

def get_conversation_state(db: Session, conversation: Conversation) -> str:
    """
    Determina el estado actual de la conversación basado en los mensajes.
    
    Esta es una versión simplificada. En producción, deberías almacenar
    el estado en la base de datos o usar un sistema más sofisticado.
    
    Args:
        db: Sesión de base de datos
        conversation: Objeto de conversación
        
    Returns:
        str: Estado actual de la conversación
    """
    # Si la conversación está bloqueada o completada
    if conversation.status in [ConversationStatus.BLOCKED, ConversationStatus.SUSPICIOUS]:
        return ConversationState.BLOCKED
    elif conversation.status == ConversationStatus.COMPLETED:
        return ConversationState.COMPLETED
    
    # Obtener mensajes de la conversación
    messages = db.query(repositories.Message).filter(
        repositories.Message.conversation_id == conversation.id
    ).order_by(repositories.Message.created_at.asc()).all()
    
    # Si no hay mensajes, es una conversación nueva
    if not messages:
        return ConversationState.INITIAL
    
    # Si solo hay un mensaje del bot (inicial), estamos en greeting
    if len(messages) == 1 and not messages[0].is_from_customer:
        return ConversationState.GREETING
    
    # Buscar indicadores en los últimos mensajes del bot
    bot_messages = [m for m in messages if not m.is_from_customer]
    if bot_messages:
        last_bot_message = bot_messages[-1].content.lower()
        
        # Detectar estado basado en el contenido del último mensaje del bot
        if "¿deseas continuar con tu compra?" in last_bot_message:
            return ConversationState.CONSENT
        elif "necesito tu nombre y dni" in last_bot_message or "ingresa tu nombre" in last_bot_message:
            return ConversationState.REGISTRATION
        elif "aquí está nuestro menú" in last_bot_message or "estos son nuestros productos" in last_bot_message:
            return ConversationState.MENU
        elif "¿qué productos deseas añadir" in last_bot_message:
            return ConversationState.PRODUCT_SELECTION
        elif "tu pedido actual es" in last_bot_message:
            return ConversationState.CART
        elif "¿deseas confirmar" in last_bot_message:
            return ConversationState.CHECKOUT
        elif "link de pago" in last_bot_message:
            return ConversationState.PAYMENT
    
    # Fallback: asumimos que estamos en selección de productos
    return ConversationState.MENU

def process_message(
    db: Session,
    customer: Customer,
    conversation: Conversation,
    message_text: str,
    threat_analysis: Optional[Dict[str, Any]] = None
) -> str:
    """
    Procesa un mensaje entrante y genera una respuesta.
    
    Esta es la función principal que maneja el flujo de conversación
    y determina cómo responder a cada mensaje del usuario.
    
    Args:
        db: Sesión de base de datos
        customer: Cliente que envió el mensaje
        conversation: Conversación activa
        message_text: Texto del mensaje
        threat_analysis: Análisis de amenazas (opcional)
        
    Returns:
        str: Respuesta para enviar al usuario
    """
    # Normalizar mensaje (minúsculas, sin espacios extra)
    normalized_message = message_text.lower().strip()
    
    # Si hay análisis de amenazas y es una amenaza alta
    if threat_analysis and threat_analysis.get("score", 0) >= 0.8:
        return responses.get_security_warning()
    
    # Determinar estado actual de la conversación
    state = get_conversation_state(db, conversation)
    
    # Manejar el mensaje según el estado de la conversación
    if state == ConversationState.INITIAL or state == ConversationState.GREETING:
        # Es el primer mensaje, enviar saludo y solicitar consentimiento
        return responses.get_greeting()
    
    elif state == ConversationState.CONSENT:
        # Usuario debe dar consentimiento para continuar
        if any(keyword in normalized_message for keyword in ["si", "sí", "ok", "dale", "claro", "acepto"]):
            # Dio consentimiento, solicitar datos básicos
            return responses.get_registration_request()
        else:
            # No dio consentimiento claro
            return responses.get_consent_clarification()
    
    elif state == ConversationState.REGISTRATION:
        # Usuario debe proporcionar nombre y DNI
        name_match = re.search(r'(?:me llamo|soy|nombre[:]?\s*)([A-Za-z\s]+)', normalized_message)
        dni_match = re.search(r'(?:mi dni[:]?\s*|dni[:]?\s*)(\d{8})', normalized_message)
        
        # Si proporcionó nombre, actualizar cliente
        if name_match:
            customer_name = name_match.group(1).strip().title()
            repositories.update_customer(db, customer.id, {"name": customer_name})
        
        # Si proporcionó DNI, actualizar cliente
        if dni_match:
            customer_dni = dni_match.group(1).strip()
            repositories.update_customer(db, customer.id, {"dni": customer_dni})
        
        # Si proporcionó ambos o ya tenemos alguno guardado
        updated_customer = repositories.get_customer_by_phone(db, customer.phone_number)
        if (name_match or updated_customer.name) and (dni_match or updated_customer.dni):
            # Mostrar menú de productos
            available_products = repositories.get_all_active_products(db)
            return responses.get_product_menu(available_products)
        else:
            # Solicitar los datos que faltan
            if not updated_customer.name:
                return "Por favor, ingresa tu nombre para continuar."
            else:
                return "Por favor, ingresa tu DNI para continuar."
    
    elif state == ConversationState.MENU or state == ConversationState.PRODUCT_SELECTION:
        # Usuario está seleccionando productos
        # Esta es una implementación básica, en producción usarías IA o NLP más avanzado
        
        # Buscar códigos de producto o nombres en el mensaje
        product_codes = re.findall(r'\b([A-Z]\d{2,3})\b', message_text)  # Códigos como A01, B123
        
        # Si encontramos códigos, añadir productos al carrito
        if product_codes:
            # Usar la función add_to_cart para añadir productos
            cart_result = repositories.add_to_cart(db, customer.id, product_codes)
            
            if cart_result["status"] == "success":
                # Obtener información del carrito actualizado
                items = cart_result["all_items"]
                total = cart_result["total_amount"]
                
                # Mostrar resumen del carrito
                return responses.get_cart_summary(items, total)
            else:
                return "Lo siento, hubo un problema al añadir los productos. Por favor, intenta de nuevo."
        
        # Si no hay códigos, intentar usar IA para entender la intención
        # En este MVP, simulamos una respuesta simple
        if any(keyword in normalized_message for keyword in ["carrito", "checkout", "pagar", "comprar", "finalizar"]):
            # Usuario quiere ver su carrito o pagar
            cart_result = repositories.get_cart(db, customer.id)
            
            if cart_result["status"] == "success" and cart_result["items"]:
                # Hay productos en el carrito
                return responses.get_cart_summary(cart_result["items"], cart_result["total_amount"])
            else:
                # Carrito vacío
                return "Tu carrito está vacío. Por favor, añade algunos productos del menú para continuar."
        elif any(keyword in normalized_message for keyword in ["menú", "productos", "opciones", "catálogo"]):
            # Usuario quiere ver el menú de nuevo
            available_products = repositories.get_all_active_products(db)
            return responses.get_product_menu(available_products)
        else:
            # Usar IA para generar una respuesta contextual
            conversation_history = []
            bot_messages = []
            
            # Obtener historial de conversación para contexto
            messages = db.query(repositories.Message).filter(
                repositories.Message.conversation_id == conversation.id
            ).order_by(repositories.Message.created_at.asc()).limit(10).all()
            
            for msg in messages:
                role = "user" if msg.is_from_customer else "assistant"
                conversation_history.append({"role": role, "content": msg.content})
                if role == "assistant":
                    bot_messages.append(msg.content)
            
            # Obtener productos disponibles
            available_products = repositories.get_all_active_products(db)
            product_list = [
                {
                    "name": p.name,
                    "code": p.code,
                    "price": p.price,
                    "description": p.description
                }
                for p in available_products
            ]
            
            is_suspicious = threat_analysis and threat_analysis.get("score", 0) >= 0.4
            
            # Generar respuesta con IA
            ai_response = openai_service.generate_response(
                customer_name=customer.name or "Cliente",
                customer_message=message_text,
                conversation_history=conversation_history,
                available_products=product_list,
                is_suspicious=is_suspicious
            )
            
            return ai_response
    
    elif state == ConversationState.CHECKOUT:
        # Usuario está confirmando el pedido
        if any(keyword in normalized_message for keyword in ["si", "sí", "confirmar", "aceptar", "ok"]):
            # Generar link de pago (en un sistema real)
            return "¡Perfecto! Aquí está tu link de pago: https://ejemplo.com/pago. Una vez realizado el pago, recibirás la confirmación por este mismo canal."
        elif any(keyword in normalized_message for keyword in ["no", "cancelar", "modificar", "cambiar"]):
            return "Entendido. ¿Qué deseas modificar en tu pedido?"
    
    # Respuesta por defecto si no se cumple ninguna condición anterior
    return responses.get_fallback_response()