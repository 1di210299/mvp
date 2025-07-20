"""
Servicio de IA para procesar confirmaciones de órdenes de compra por WhatsApp
Analiza mensajes de texto, imágenes y confirma recepciones
"""
import logging
import json
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class PurchaseOrderAIService:
    """Servicio de IA para analizar confirmaciones de órdenes de compra"""
    
    def __init__(self):
        self.client = None
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Inicializar cliente OpenAI"""
        try:
            import openai
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client inicializado para análisis de órdenes")
            else:
                logger.warning("❌ OPENAI_API_KEY no configurado")
        except ImportError:
            logger.warning("❌ openai package no instalado")
    
    def analyze_whatsapp_message(self, message_text, purchase_order, sender_phone):
        """
        Analizar mensaje de WhatsApp para detectar confirmaciones/rechazos de órdenes
        """
        try:
            if not self.client:
                return self._analyze_message_basic(message_text, purchase_order)
            
            prompt = f"""
Analiza este mensaje de WhatsApp del proveedor sobre una orden de compra:

ORDEN DE COMPRA:
- Número: {purchase_order.order_number}
- Producto: {purchase_order.product.name}
- Cantidad: {purchase_order.quantity}
- Total: S/ {purchase_order.total_amount}
- Empresa: {purchase_order.company.name}

MENSAJE DEL PROVEEDOR:
"{message_text}"

TELÉFONO DEL PROVEEDOR: {sender_phone}

Determina si el mensaje contiene:
1. CONFIRMACIÓN de la orden (sí/no)
2. RECHAZO de la orden (sí/no)
3. PRECIO alternativo propuesto
4. TIEMPO DE ENTREGA confirmado
5. CONDICIONES especiales
6. SOLICITUD de más información

Responde en JSON con esta estructura:
{{
    "action": "confirmed|rejected|negotiating|requesting_info|unclear",
    "confidence": 0.95,
    "confirmed": true/false,
    "price_proposed": null o número,
    "delivery_days": null o número,
    "conditions": "texto con condiciones especiales",
    "next_action": "descripción de qué hacer",
    "summary": "resumen del mensaje en español"
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Validar estructura de respuesta
            required_fields = ['action', 'confidence', 'confirmed']
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = None
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analizando mensaje con IA: {str(e)}")
            return self._analyze_message_basic(message_text, purchase_order)
    
    def _analyze_message_basic(self, message_text, purchase_order):
        """Análisis básico sin IA (fallback)"""
        text_lower = message_text.lower()
        
        # Palabras clave de confirmación
        confirm_keywords = ['acepto', 'confirmo', 'ok', 'sí', 'si', 'perfecto', 'de acuerdo', 'está bien']
        reject_keywords = ['no puedo', 'rechazo', 'no', 'imposible', 'no tengo', 'agotado']
        
        confirmed = any(keyword in text_lower for keyword in confirm_keywords)
        rejected = any(keyword in text_lower for keyword in reject_keywords)
        
        if confirmed:
            action = "confirmed"
        elif rejected:
            action = "rejected"
        else:
            action = "unclear"
        
        return {
            "action": action,
            "confidence": 0.7,
            "confirmed": confirmed,
            "price_proposed": None,
            "delivery_days": None,
            "conditions": None,
            "next_action": "Procesar respuesta básica",
            "summary": f"Análisis básico: {action}"
        }
    
    def analyze_delivery_photo(self, image_url, purchase_order):
        """
        Analizar foto de entrega usando OpenAI Vision
        """
        try:
            logger.info(f"🖼️ Analizando foto de entrega para orden {purchase_order.order_number}")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Modelo con capacidad de visión
                messages=[
                    {
                        "role": "system",
                        "content": f"""
Eres un experto analizando fotos de entrega de productos. 

ORDEN DE COMPRA:
- Número: {purchase_order.order_number}
- Producto: {purchase_order.product.name}
- Cantidad: {purchase_order.quantity}
- Descripción: {purchase_order.product.description}

INSTRUCCIONES:
1. Analiza la imagen para verificar si corresponde a una entrega real
2. Identifica productos visibles en la imagen
3. Evalúa la calidad de la entrega (empaque, condición, etc.)
4. Detecta posibles problemas (daños, cantidad incorrecta, etc.)

RESPONDE en JSON con esta estructura exacta:
{{
    "is_valid_delivery": true/false,
    "confidence": 0.0-1.0,
    "products_detected": ["producto1", "producto2"],
    "quantity_visible": number,
    "delivery_quality": "excellent/good/fair/poor",
    "issues_detected": ["problema1", "problema2"],
    "verification_summary": "resumen en español"
}}
"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analiza esta foto de entrega para la orden {purchase_order.order_number}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extraer JSON de la respuesta
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            analysis = json.loads(content)
            
            logger.info(f"✅ Análisis de foto completado: {analysis.get('verification_summary')}")
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing JSON de análisis de foto: {str(e)}")
            return {
                "is_valid_delivery": False,
                "confidence": 0.0,
                "products_detected": [],
                "quantity_visible": 0,
                "delivery_quality": "unknown",
                "issues_detected": ["Error en análisis de IA"],
                "verification_summary": "No se pudo analizar la imagen correctamente"
            }
            
        except Exception as e:
            logger.error(f"❌ Error analizando foto de entrega: {str(e)}")
            return {
                "is_valid_delivery": False,
                "confidence": 0.0,
                "products_detected": [],
                "quantity_visible": 0,
                "delivery_quality": "error",
                "issues_detected": [f"Error técnico: {str(e)}"],
                "verification_summary": "Error técnico al analizar la imagen"
            }
    
    def _analyze_photo_basic(self, purchase_order):
        """Análisis básico de foto (fallback)"""
        return {
            "delivery_confirmed": True,
            "quantity_delivered": purchase_order.quantity,
            "quality_ok": True,
            "observations": "Análisis básico - foto recibida",
            "confidence": 0.6,
            "next_action": "Validación manual requerida"
        }
    
    def generate_follow_up_message(self, purchase_order, analysis_result):
        """
        Generar mensaje de seguimiento basado en el análisis
        """
        try:
            if not self.client:
                return self._generate_follow_up_basic(analysis_result)
            
            prompt = f"""
Genera un mensaje de WhatsApp profesional y cordial para responder al proveedor:

ORDEN: {purchase_order.order_number}
PRODUCTO: {purchase_order.product.name}
ANÁLISIS: {analysis_result.get('summary', '')}
ACCIÓN: {analysis_result.get('action', '')}

El mensaje debe:
- Ser breve y profesional
- Confirmar la respuesta del proveedor
- Indicar próximos pasos si es necesario
- Mantener un tono cordial

Responde solo el texto del mensaje, sin comillas.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generando follow-up: {str(e)}")
            return self._generate_follow_up_basic(analysis_result)
    
    def _generate_follow_up_basic(self, analysis_result):
        """Mensaje de seguimiento básico"""
        action = analysis_result.get('action', 'unclear')
        
        messages = {
            'confirmed': '✅ Perfecto! Hemos confirmado su aceptación de la orden. Gracias!',
            'rejected': '❌ Entendido. Tomaremos nota del rechazo de la orden.',
            'negotiating': '💬 Hemos recibido su propuesta. La revisaremos pronto.',
            'unclear': '❓ Hemos recibido su mensaje. Si puede confirmar su respuesta sería de gran ayuda.'
        }
        
        return messages.get(action, messages['unclear'])


# Instancia global para uso en views
purchase_order_ai_service = PurchaseOrderAIService()
