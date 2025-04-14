import logging
import json
from typing import Dict, Any, List, Optional, Union

import openai
from app.config import OPENAI_API_KEY

# Configurar OpenAI API
openai.api_key = OPENAI_API_KEY

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
        # Reemplazar placeholder en la plantilla
        prompt = prompt_template.replace("{{text}}", text)
        
        # Llamar a la API de OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Puedes usar gpt-4 para mejores resultados
            temperature=temperature,
            messages=[
                {"role": "system", "content": "Eres un asistente de análisis de texto especializado en evaluar amenazas y extorsiones."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Extraer contenido JSON
        content = response.choices[0].message.content
        
        # Intentar parsear la respuesta como JSON
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar respuesta JSON: {content}")
            return {"error": "Formato de respuesta inválido", "raw_content": content}
        
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
    prompt_template = """
    Analiza el siguiente texto para determinar si contiene amenazas, intentos de extorsión, 
    lenguaje violento o cualquier otro contenido que podría indicar un comportamiento peligroso.
    
    Texto: "{{text}}"
    
    Responde en formato JSON con la siguiente estructura:
    {
        "score": (float entre 0 y 1, donde 0 es no amenazante y 1 es extremadamente peligroso),
        "is_threat": (booleano: true si parece una amenaza, false si no),
        "threat_type": (string: tipo de amenaza, puede ser "extorsión", "violencia", "intimidación", "ninguna", etc.),
        "keywords": (array de strings: palabras clave que indican una posible amenaza),
        "explanation": (string: explicación breve de por qué se considera o no una amenaza)
    }
    
    Considera palabras en jerga peruana y términos locales de extorsión.
    """
    
    return analyze_text(text, prompt_template)

def generate_response(
    customer_name: str, 
    customer_message: str, 
    conversation_history: List[Dict[str, str]],
    available_products: Optional[List[Dict[str, Any]]] = None,
    is_suspicious: bool = False
) -> str:
    """
    Genera una respuesta para el cliente basada en su mensaje y el historial.
    
    Args:
        customer_name: Nombre del cliente (o "Cliente" si no hay nombre)
        customer_message: Mensaje actual del cliente
        conversation_history: Lista de mensajes anteriores en formato [{"role": "user"/"assistant", "content": "..."}]
        available_products: Lista opcional de productos disponibles para mencionar
        is_suspicious: Indica si el mensaje del cliente se considera sospechoso
        
    Returns:
        str: Respuesta generada para el cliente
    """
    try:
        system_message = """Eres un asistente de ventas amable y eficiente para una tienda online en Perú.
        Tu objetivo es ayudar a los clientes a encontrar productos, responder preguntas y guiarlos para completar su compra.
        
        Directrices:
        1. Sé amable, respetuoso y profesional en todo momento.
        2. Proporciona respuestas breves y directas.
        3. Si el cliente pregunta por productos, menciona su precio y disponibilidad.
        4. No inventes productos o precios que no estén en tu lista.
        5. Evita hacer promesas sobre plazos de entrega específicos.
        6. Nunca pidas datos personales como números de tarjeta o contraseñas.
        7. Si el cliente muestra señales de comportamiento sospechoso, mantén la conversación profesional y evita confrontaciones.
        
        Para comprar, el cliente puede elegir productos por código o nombre, y recibirá un enlace de pago cuando confirme su pedido."""
        
        # Añadir información de productos si está disponible
        if available_products:
            products_info = "Productos disponibles:\n"
            for product in available_products:
                products_info += f"- {product['name']} (Código: {product['code']}): S/{product['price']:.2f}\n"
            system_message += "\n\n" + products_info
        
        # Ajustar prompt si el mensaje es sospechoso
        if is_suspicious:
            system_message += "\n\nATENCIÓN: El mensaje del cliente puede contener lenguaje sospechoso o amenazante. Mantén la calma, sé profesional, y evita escalaciones. No confrontes al cliente sobre esto, pero mantén tus respuestas neutras y orientadas a los procesos estándar de la tienda."
        
        messages = [{"role": "system", "content": system_message}]
        
        # Añadir historial de conversación
        messages.extend(conversation_history)
        
        # Añadir mensaje actual
        messages.append({"role": "user", "content": customer_message})
        
        # Llamar a la API de OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Puedes usar gpt-4 para mejor calidad
            temperature=0.7,
            messages=messages,
            max_tokens=300  # Limitar longitud de respuesta
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generando respuesta con OpenAI: {str(e)}")
        # Respuesta fallback en caso de error
        return "Lo siento, estamos experimentando problemas técnicos. Por favor, intenta nuevamente en unos momentos o contáctanos por otro medio."