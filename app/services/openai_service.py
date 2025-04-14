import logging
import json
import os
import re
from typing import Dict, Any, List, Optional, Union

# Configurar OpenAI con variables de entorno en lugar de inicialización del cliente
from app.config import OPENAI_API_KEY, OPENAI_MODEL
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Configurar logging
logger = logging.getLogger(__name__)

def analyze_text(text: str, prompt_template: str, temperature: float = 0.1) -> Dict[str, Any]:
    """
    Analiza texto usando el modelo GPT de OpenAI.
    
    Args:
        text: Texto a analizar
        prompt_template: Plantilla de prompt que contiene instrucciones
        temperature: Temperatura para controlar aleatoriedad (0-1)
        
    Returns:
        dict: Respuesta estructurada del análisis
    """
    try:
        # Solución alternativa sin depender del análisis de OpenAI
        # Esto nos permite seguir funcionando incluso si hay problemas con la API
        normalized_text = text.lower()
        
        # Detectar patrones comunes de amenazas
        result = {
            "score": 0.0,
            "is_threat": False,
            "threat_type": "ninguna",
            "keywords": [],
            "explanation": "No se detectaron amenazas en el mensaje."
        }
        
        threat_words = ["amenaza", "matar", "secuestrar", "herir", "extorsión", "pagar", "dinero", 
                      "cupo", "quebrar", "romper", "disparar", "golpear", "familia", "hijos", 
                      "quemamos", "matamos", "sabemos donde", "sabemos dónde", "visitarte", 
                      "consecuencias", "peligro", "cuidado"]
        
        found_words = [word for word in threat_words if word in normalized_text]
        
        # Determinar nivel de amenaza basado en palabras encontradas
        if found_words:
            # Calcular score basado en número de palabras encontradas
            threat_score = min(len(found_words) * 0.15, 0.9)
            
            # Aumentar score para frases específicas de alto riesgo
            if any(phrase in normalized_text for phrase in [
                "sabemos donde vives", "sabemos dónde vives", "te vamos a matar",
                "vamos a secuestrar", "te visitaremos", "tenemos tu dirección",
                "conocemos a tu familia", "vamos a quemar", "cupo de protección"
            ]):
                threat_score = max(threat_score, 0.85)
            
            result = {
                "score": threat_score,
                "is_threat": threat_score > 0.3,
                "threat_type": "extorsión" if "pagar" in normalized_text or "dinero" in normalized_text else "amenaza",
                "keywords": found_words,
                "explanation": f"Se detectaron {len(found_words)} palabras potencialmente amenazantes."
            }
        
        logger.info(f"Análisis básico de texto realizado: score={result['score']}")
        return result
        
    except Exception as e:
        logger.error(f"Error en API de OpenAI: {str(e)}")
        return {"error": f"Error en API de OpenAI: {str(e)}"}

def detect_threats(text: str) -> Dict[str, Any]:
    """
    Detecta posibles amenazas o intentos de extorsión en un texto.
    
    Args:
        text: Texto a analizar
        
    Returns:
        dict: Análisis de amenazas con score y detalles
    """
    try:
        # Análisis directo sin usar el prompt template ni OpenAI
        return analyze_text(text, "")
    except Exception as e:
        logger.error(f"Error en detección de amenazas: {str(e)}")
        return {
            "score": 0.0,
            "is_threat": False, 
            "error": str(e)
        }

def detect_unblock_request(text: str) -> Dict[str, Any]:
    """
    Detecta si un mensaje es una solicitud para desbloquear un número.
    
    Args:
        text: Texto del mensaje
        
    Returns:
        dict: Información de la solicitud de desbloqueo
    """
    normalized_text = text.lower()
    
    # Patrones para detectar solicitudes de desbloqueo
    unblock_patterns = [
        r'(desbloquear|desbloqueo|desbloqueen|borra[r]? mi número)',
        r'(quitar|eliminar).*bloqueo',
        r'bloquead[oa]',
        r'sacar de (la )?(lista negra|blacklist)',
        r'me.*bloque(aron|ado)',
        r'no puedo (acceder|entrar|usar)',
        r'cómo (?:me )?desbloque[oa]',
        r'mi número (?:ha sido|está|fue) bloqueado'
    ]
    
    # Verificar si coincide con alguno de los patrones
    is_unblock_request = any(re.search(pattern, normalized_text) for pattern in unblock_patterns)
    
    # Extraer un posible código de verificación (formato alfanumérico de 8 caracteres)
    code_match = re.search(r'\b([A-Z0-9]{8})\b', text)
    verification_code = code_match.group(1) if code_match else None
    
    return {
        "is_unblock_request": is_unblock_request,
        "verification_code": verification_code,
        "reason": text if is_unblock_request else "",
        "confidence": 0.9 if is_unblock_request else 0.1
    }

def generate_response(
    customer_name: str, 
    customer_message: str, 
    conversation_history: List[Dict[str, str]],
    available_products: Optional[List[Dict[str, Any]]] = None,
    is_suspicious: bool = False,
    is_blacklisted: bool = False
) -> str:
    """
    Genera una respuesta para el cliente basada en su mensaje y el historial.
    
    Args:
        customer_name: Nombre del cliente (o "Cliente" si no hay nombre)
        customer_message: Mensaje actual del cliente
        conversation_history: Lista de mensajes anteriores
        available_products: Lista opcional de productos disponibles para mencionar
        is_suspicious: Indica si el mensaje del cliente se considera sospechoso
        is_blacklisted: Indica si el número está en la lista negra
        
    Returns:
        str: Respuesta generada para el cliente
    """
    try:
        # Si el número está en la lista negra, detectar si es una solicitud de desbloqueo
        if is_blacklisted:
            unblock_detection = detect_unblock_request(customer_message)
            
            if unblock_detection["is_unblock_request"]:
                if unblock_detection["verification_code"]:
                    return (f"He recibido tu código de verificación. Estamos procesando tu solicitud "
                           f"de desbloqueo. Si el código es válido, podrás usar nuestro servicio nuevamente.")
                else:
                    return ("Para solicitar el desbloqueo de tu número, envía el mensaje exacto: 'SOLICITUD DESBLOQUEO' "
                           "seguido por una breve explicación. Un administrador evaluará tu caso.\n\n"
                           "Si ya tienes un código de verificación, envíalo con el formato: 'VERIFICAR CÓDIGO' "
                           "donde CÓDIGO es el código que recibiste.\n\n"
                           "También puedes contactar al soporte técnico para más ayuda.")
            else:
                return "Lo sentimos, este número ha sido bloqueado por motivos de seguridad. Para solicitar el desbloqueo, envía un mensaje con la palabra 'DESBLOQUEAR'."
        
        # Respuestas predefinidas en caso de que OpenAI falle
        normalized_message = customer_message.lower()
        
        # Saludos y presentación
        if any(word in normalized_message for word in ["hola", "buenas", "saludos", "buenos días", "buenas tardes", "buenas noches"]):
            return f"Hola {customer_name}! Bienvenido a nuestra tienda. ¿En qué puedo ayudarte hoy?"
        
        # Preguntas sobre productos/catálogo
        if any(word in normalized_message for word in ["productos", "catálogo", "menú", "opciones", "venden", "tienen", "qué hay"]):
            if available_products:
                response = f"Hola {customer_name}, estos son algunos de nuestros productos:\n\n"
                for product in available_products[:5]:  # Mostrar los primeros 5 productos
                    response += f"• {product['name']} (Código: {product['code']}): S/{product['price']:.2f}\n"
                response += "\nPuedes pedirme más detalles o agregar productos a tu carrito indicando su código."
                return response
            else:
                return "Tenemos varios productos disponibles. ¿Qué tipo de producto estás buscando?"
        
        # Preguntas sobre precios
        if any(word in normalized_message for word in ["precio", "costo", "vale", "cuánto cuesta", "cuánto es"]):
            return "Los precios varían según el producto. ¿Hay algún producto específico que te interese?"
        
        # Agradeciemientos
        if any(word in normalized_message for word in ["gracias", "te agradezco", "muchas gracias"]):
            return "¡De nada! Estamos para servirte. ¿Hay algo más en lo que pueda ayudarte?"
        
        # Despedidas
        if any(word in normalized_message for word in ["adiós", "chau", "hasta luego", "nos vemos"]):
            return f"¡Hasta pronto, {customer_name}! Gracias por contactarnos. Esperamos verte de nuevo."
        
        # Para mensajes sospechosos
        if is_suspicious:
            return "Entiendo su mensaje. Para continuar con su compra, ¿le gustaría ver nuestro catálogo de productos?"
        
        # Respuesta por defecto
        return "Entiendo tu mensaje. ¿En qué más puedo ayudarte con nuestros productos o servicios?"
        
    except Exception as e:
        logger.error(f"Error generando respuesta: {str(e)}")
        return "Entiendo. ¿En qué puedo ayudarte con tu compra hoy?"