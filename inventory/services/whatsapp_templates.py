"""
Templates de WhatsApp para diferentes tipos de mensajes
"""

class WhatsAppTemplates:
    """Templates para mensajes WhatsApp"""
    
    @staticmethod
    def purchase_order_template(purchase_order):
        """Template para órdenes de compra"""
        priority_emoji = {
            'low': '🔵',
            'medium': '🟡', 
            'high': '🟠',
            'urgent': '🔴'
        }
        
        emoji = priority_emoji.get(purchase_order.priority, '📋')
        
        # Template más profesional y estructurado
        template = f"""{emoji} *ORDEN DE COMPRA*

*#{purchase_order.order_number}*
{purchase_order.company.name}

┌─ 📦 *PRODUCTO*
│ • {purchase_order.product.name}
│ • SKU: {purchase_order.product.sku}
│ • Cantidad: *{purchase_order.quantity} unidades*
│ • Precio unit.: S/ {purchase_order.unit_price}
└─ *TOTAL: S/ {purchase_order.total_amount}*

┌─ ⏰ *DETALLES*
│ • Prioridad: {purchase_order.get_priority_display()}
│ • Fecha esperada: {purchase_order.expected_delivery_date or 'Por coordinar'}
│ • Empresa: {purchase_order.company.name}
└─ • Fecha orden: {purchase_order.created_at.strftime('%d/%m/%Y')}

┌─ ✅ *FAVOR CONFIRMAR:*
│ 1️⃣ Disponibilidad del producto
│ 2️⃣ Tiempo de entrega
│ 3️⃣ Condiciones de pago
└─ 4️⃣ Datos para coordinación

📞 *Contacto:*
{getattr(purchase_order.company, 'phone', 'No especificado')}

_Responda con "CONFIRMADO" para aceptar_
_Sistema automático DataLens_"""
        
        return template
    
    @staticmethod
    def order_confirmation_template(purchase_order):
        """Template para confirmación de orden"""
        return f"""✅ *ORDEN CONFIRMADA*

Gracias por confirmar la orden #{purchase_order.order_number}

*Próximos pasos:*
• Preparación del pedido
• Coordinación de entrega
• Seguimiento automático

*Datos de contacto:*
📞 {getattr(purchase_order.company, 'phone', 'No especificado')}
📧 {getattr(purchase_order.company, 'email', 'No especificado')}

Recibirá actualizaciones automáticas del estado de su orden.

_Sistema DataLens_"""
    
    @staticmethod
    def order_reminder_template(purchase_order, days_pending):
        """Template para recordatorios de orden"""
        return f"""⏰ *RECORDATORIO ORDEN*

Su orden #{purchase_order.order_number} está pendiente hace {days_pending} días.

*Producto:* {purchase_order.product.name}
*Cantidad:* {purchase_order.quantity} unidades
*Total:* S/ {purchase_order.total_amount}

Por favor confirme:
• Estado de disponibilidad
• Tiempo de entrega estimado

*¿Necesita modificar algo?*
Responda este mensaje o contáctenos.

_Sistema DataLens_"""
    
    @staticmethod
    def welcome_supplier_template(supplier_name):
        """Template de bienvenida para nuevos proveedores"""
        return f"""👋 *¡Bienvenido a DataLens!*

Hola *{supplier_name}*,

Ahora recibirá órdenes de compra automáticas por WhatsApp.

*Comandos útiles:*
• "CONFIRMADO" - Confirmar orden
• "NO DISPONIBLE" - Rechazar orden  
• "PRECIO" - Consultar precios
• "TIEMPO" - Consultar entregas
• "CONTACTO" - Hablar con una persona

*Ventajas:*
✅ Órdenes instantáneas
✅ Seguimiento automático
✅ Comunicación directa
✅ Histórico de pedidos

¡Esperamos una excelente colaboración!

_Sistema DataLens_"""
    
    @staticmethod
    def auto_response_template(message_type):
        """Templates para respuestas automáticas"""
        
        templates = {
            'welcome': """¡Hola! 👋

Soy el asistente automático de DataLens.

📋 *Comandos disponibles:*
• CONFIRMADO - Confirmar orden
• PRECIO - Consultar precios  
• TIEMPO - Tiempo de entrega
• CONTACTO - Hablar con persona
• AYUDA - Ver todos los comandos

¿En qué puedo ayudarte?""",
            
            'confirmed': """✅ *Confirmación recibida*

Gracias por confirmar la disponibilidad.

Por favor proporciona:
• ⏰ Tiempo de entrega estimado
• 💰 Condiciones de pago
• 🚚 Detalles de envío

Un miembro de nuestro equipo se contactará pronto.""",
            
            'price_inquiry': """💰 *Consulta de precios*

Para cotizaciones precisas, un miembro de nuestro equipo se contactará contigo.

📞 También puedes llamarnos para consultas urgentes.

Gracias por tu interés.""",
            
            'delivery_inquiry': """⏰ *Consulta de tiempo de entrega*

Por favor indica el tiempo estimado de entrega para esta orden.

Nuestro equipo tomará nota y actualizará el sistema.

Gracias por tu respuesta.""",
            
            'human_contact': """👥 *Contacto humano*

Te conectaremos con una persona de nuestro equipo de compras.

Espera una llamada o mensaje directo en los próximos minutos.

Gracias por tu paciencia.""",
            
            'help': """🆘 *Comandos disponibles:*

• *CONFIRMADO* - Confirmar orden de compra
• *NO DISPONIBLE* - Rechazar por falta de stock
• *PRECIO* - Consultar precios especiales
• *TIEMPO* - Informar tiempo de entrega
• *CONTACTO* - Hablar con una persona
• *ESTADO* - Ver estado de órdenes

*Para órdenes específicas:*
• Incluye el número de orden (ej: #PO-2025-01-19-0001)

_Sistema DataLens_""",
            
            'not_available': """❌ *Producto no disponible*

Hemos registrado que este producto no está disponible.

*Opciones:*
1. ¿Cuándo estará disponible?
2. ¿Hay algún producto similar?
3. ¿Podemos hacer pedido anticipado?

Un miembro del equipo se contactará para buscar alternativas.

Gracias por informarnos.""",
            
            'default': """📱 *Mensaje recibido*

Hemos registrado tu mensaje. Un miembro de nuestro equipo se contactará pronto.

*Para respuestas rápidas:*
• CONFIRMADO - Confirmar orden
• AYUDA - Ver comandos
• CONTACTO - Hablar con persona

Gracias."""
        }
        
        return templates.get(message_type, templates['default'])
    
    @staticmethod
    def order_status_update_template(purchase_order, new_status):
        """Template para actualizaciones de estado"""
        status_emoji = {
            'confirmed': '✅',
            'in_transit': '🚚',
            'delivered': '📦',
            'cancelled': '❌'
        }
        
        emoji = status_emoji.get(new_status, '📋')
        status_text = dict(purchase_order.STATUS_CHOICES).get(new_status, new_status)
        
        return f"""{emoji} *ACTUALIZACIÓN DE ORDEN*

Orden #{purchase_order.order_number}
*Estado:* {status_text}

*Producto:* {purchase_order.product.name}
*Cantidad:* {purchase_order.quantity} unidades

{WhatsAppTemplates._get_status_specific_message(new_status, purchase_order)}

_Sistema DataLens_"""
    
    @staticmethod
    def _get_status_specific_message(status, purchase_order):
        """Mensaje específico según el estado"""
        if status == 'confirmed':
            return """*¡Excelente!* 
Su orden ha sido confirmada y está en proceso.
Recibirá actualizaciones del progreso."""
        
        elif status == 'in_transit':
            return """*En camino* 🚚
Su pedido está siendo enviado.
Tiempo estimado de llegada será confirmado."""
        
        elif status == 'delivered':
            return """*¡Entregado!* 📦
Su pedido ha sido entregado exitosamente.
Gracias por su confianza."""
        
        elif status == 'cancelled':
            return """*Orden cancelada*
Esta orden ha sido cancelada.
Para consultas, contáctenos directamente."""
        
        return "Estado actualizado en el sistema."


class WhatsAppMessageProcessor:
    """Procesador inteligente de mensajes WhatsApp"""
    
    @staticmethod
    def process_message(message_text, supplier=None):
        """Procesar mensaje y determinar tipo de respuesta"""
        message_lower = message_text.lower().strip()
        
        # Detectar números de orden
        import re
        order_pattern = r'#?PO-\d{4}-\d{2}-\d{2}-\d{4}'
        order_match = re.search(order_pattern, message_text, re.IGNORECASE)
        
        # Mapeo de palabras clave a tipos de respuesta
        keyword_map = {
            'confirmado': 'confirmed',
            'confirmo': 'confirmed', 
            'disponible': 'confirmed',
            'ok': 'confirmed',
            'sí': 'confirmed',
            'si': 'confirmed',
            
            'no disponible': 'not_available',
            'agotado': 'not_available',
            'sin stock': 'not_available',
            'no tengo': 'not_available',
            
            'precio': 'price_inquiry',
            'costo': 'price_inquiry',
            'cotización': 'price_inquiry',
            'cotizar': 'price_inquiry',
            
            'tiempo': 'delivery_inquiry',
            'entrega': 'delivery_inquiry',
            'cuándo': 'delivery_inquiry',
            'cuando': 'delivery_inquiry',
            
            'contacto': 'human_contact',
            'persona': 'human_contact',
            'humano': 'human_contact',
            
            'ayuda': 'help',
            'comandos': 'help',
            'help': 'help',
            
            'hola': 'welcome',
            'hi': 'welcome',
            'hello': 'welcome',
            'buenas': 'welcome',
        }
        
        # Buscar coincidencias
        for keyword, response_type in keyword_map.items():
            if keyword in message_lower:
                return {
                    'type': response_type,
                    'order_number': order_match.group(0) if order_match else None,
                    'original_message': message_text,
                    'confidence': 0.9 if len(keyword) > 3 else 0.7
                }
        
        # Si no hay coincidencias, respuesta por defecto
        return {
            'type': 'default',
            'order_number': order_match.group(0) if order_match else None,
            'original_message': message_text,
            'confidence': 0.3
        }
