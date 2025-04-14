from typing import List, Dict, Any, Optional

def get_greeting() -> str:
    """Mensaje inicial de bienvenida y consentimiento."""
    return (
        "Bienvenido(a) a nuestro sistema de ventas por WhatsApp. "
        "Este canal está protegido y monitoreado para prevenir fraudes. "
        "Toda conversación es registrada. Este canal colabora con la PNP en casos de extorsión. "
        "¿Deseas continuar con tu compra? Responde *Sí* o *No*."
    )

def get_consent_clarification() -> str:
    """Mensaje para clarificar consentimiento."""
    return (
        "Para usar este servicio, necesitamos tu consentimiento explícito. "
        "Por favor, responde *Sí* si deseas continuar con tu compra o *No* para finalizar la conversación."
    )

def get_registration_request() -> str:
    """Solicitud de datos básicos del cliente."""
    return (
        "Gracias por tu consentimiento. Para continuar, necesito tu nombre y DNI. "
        "Por ejemplo: *Me llamo Juan Pérez, DNI 12345678*."
    )

def get_product_menu(products: List[Dict[str, Any]]) -> str:
    """
    Muestra el menú de productos disponibles.
    
    Args:
        products: Lista de productos disponibles
        
    Returns:
        str: Mensaje con el menú formateado
    """
    if not products:
        return (
            "Actualmente no hay productos disponibles. Por favor, intenta más tarde "
            "o contacta a nuestro soporte técnico."
        )
    
    menu = "Aquí está nuestro menú de productos disponibles:\n\n"
    
    for product in products:
        menu += f"*{product.name}* - Código: {product.code}\n"
        menu += f"Precio: S/{product.price:.2f}\n"
        if product.description:
            menu += f"{product.description}\n"
        menu += "\n"
    
    menu += (
        "Para añadir un producto a tu carrito, indica el código. "
        "Por ejemplo: *Quiero el producto A01* o *A01*.\n\n"
        "¿Qué productos deseas añadir a tu carrito?"
    )
    
    return menu

def get_cart_summary(items: List[Dict[str, Any]], total: float) -> str:
    """
    Muestra el resumen del carrito.
    
    Args:
        items: Lista de items en el carrito
        total: Monto total
        
    Returns:
        str: Mensaje con el resumen del carrito
    """
    if not items:
        return "Tu carrito está vacío. Agrega algunos productos del menú para continuar."
    
    summary = "Tu pedido actual es:\n\n"
    
    for item in items:
        summary += f"• {item['quantity']}x {item['name']} - S/{item['total']:.2f}\n"
    
    summary += f"\n*Total: S/{total:.2f}*\n\n"
    summary += "¿Deseas confirmar tu pedido? Responde *Sí* para proceder al pago o *No* para modificarlo."
    
    return summary

def get_payment_link(order_id: int, payment_link: str) -> str:
    """
    Mensaje con el link de pago.
    
    Args:
        order_id: ID de la orden
        payment_link: URL para el pago
        
    Returns:
        str: Mensaje con el link de pago
    """
    return (
        f"¡Gracias por tu pedido #{order_id}!\n\n"
        f"Aquí está tu link de pago: {payment_link}\n\n"
        f"Una vez completado el pago, recibirás la confirmación por este canal. "
        f"Si tienes algún problema, escribe *ayuda* y te asistiremos."
    )

def get_payment_confirmation(order_id: int) -> str:
    """
    Confirmación de pago recibido.
    
    Args:
        order_id: ID de la orden
        
    Returns:
        str: Mensaje de confirmación
    """
    return (
        f"¡Pago confirmado para tu pedido #{order_id}! 🎉\n\n"
        f"Tu compra está siendo procesada y recibirás pronto información sobre la entrega. "
        f"¡Gracias por tu compra!"
    )

def get_security_warning() -> str:
    """Advertencia de seguridad para mensajes sospechosos."""
    return (
        "⚠️ *AVISO IMPORTANTE* ⚠️\n\n"
        "Esta conversación está siendo monitoreada por motivos de seguridad. "
        "Si está realizando alguna amenaza o intento de extorsión, la información "
        "será enviada automáticamente a la Policía Nacional del Perú. "
        "Este número ya ha sido registrado en nuestra base de datos de seguridad."
    )

def get_blocked_message() -> str:
    """Mensaje para usuarios bloqueados."""
    return (
        "Lo sentimos, este número ha sido bloqueado por motivos de seguridad. "
        "Si consideras que esto es un error, por favor comunícate con nuestro "
        "equipo de soporte en otro canal."
    )

def get_fallback_response() -> str:
    """Respuesta genérica cuando no se entiende el mensaje."""
    return (
        "Disculpa, no pude entender tu mensaje. Por favor, indica qué "
        "productos deseas comprar o escribe *ayuda* para ver las opciones disponibles."
    )

def get_help_message() -> str:
    """Mensaje de ayuda con comandos disponibles."""
    return (
        "Aquí tienes algunas opciones que puedes usar:\n\n"
        "• *Menú* - Ver lista de productos disponibles\n"
        "• *Carrito* - Ver tu pedido actual\n"
        "• *Pagar* - Proceder al pago de tu pedido\n"
        "• *Cancelar* - Cancelar tu pedido actual\n"
        "• *Ayuda* - Ver este mensaje de ayuda\n\n"
        "También puedes escribir naturalmente y te entenderé. Por ejemplo: "
        "*Quiero añadir 2 unidades del producto A01*"
    )

def get_goodbye_message() -> str:
    """Mensaje de despedida."""
    return (
        "Gracias por contactarnos. Si necesitas realizar una compra en el futuro, "
        "estaremos aquí para atenderte. ¡Que tengas un excelente día!"
    )