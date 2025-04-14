from fastapi import APIRouter, Depends, Request, Response, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json
from typing import Dict, Any
import logging

from app.db.session import get_db
from app.db import repositories
from app.security import threat_detection
from app.bot import conversation
from app.services import twilio_service, notification_service
from app.config import TWILIO_ACCOUNT_SID

router = APIRouter()

# Configurar logging
logger = logging.getLogger(__name__)

@router.post("/twilio")
async def twilio_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook para recibir mensajes de WhatsApp a través de Twilio.
    
    Este endpoint procesa los mensajes entrantes, analiza posibles amenazas,
    maneja el flujo de conversación y responde al usuario.
    """
    form_data = await request.form()
    
    # Extraer datos del mensaje de WhatsApp
    try:
        # Obtener datos básicos
        from_number = form_data.get("From", "").strip()
        to_number = form_data.get("To", "").strip()
        message_body = form_data.get("Body", "").strip()
        
        logger.info(f"Mensaje recibido de {from_number}: {message_body[:50]}...")

        # Validar número de teléfono (normalizarlo a formato E.164)
        if from_number.startswith("whatsapp:"):
            from_number = from_number
        else:
            from_number = f"whatsapp:{from_number}"

        # Verificar autenticidad del webhook (Twilio signature)
        # Esta es una versión simplificada, en producción deberías validar 
        # la firma del webhook usando el TWILIO_AUTH_TOKEN
        account_sid = form_data.get("AccountSid")
        if account_sid != TWILIO_ACCOUNT_SID:
            logger.warning(f"Intento de webhook con SID inválido: {account_sid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autorizado"
            )
        
        # Verificar si el número está en la lista negra
        if repositories.is_phone_blacklisted(db, from_number):
            logger.warning(f"Mensaje bloqueado de número en lista negra: {from_number}")
            # Opcionalmente, enviar un mensaje de bloqueo
            background_tasks.add_task(
                twilio_service.send_message,
                to=from_number,
                message="Lo sentimos, este número ha sido bloqueado por motivos de seguridad."
            )
            return JSONResponse(
                content={"status": "blocked", "message": "Número en lista negra"},
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar/crear cliente si no existe
        customer = repositories.get_customer_by_phone(db, from_number)
        if not customer:
            customer = repositories.create_customer(db, from_number)
        
        # Verificar si el cliente está bloqueado
        if customer.is_blocked:
            logger.warning(f"Mensaje bloqueado de cliente bloqueado: {from_number}")
            background_tasks.add_task(
                twilio_service.send_message,
                to=from_number,
                message="Lo sentimos, este número ha sido bloqueado por motivos de seguridad."
            )
            return JSONResponse(
                content={"status": "blocked", "message": "Cliente bloqueado"},
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener o crear conversación activa
        active_conversation = repositories.get_active_conversation(db, customer.id)
        if not active_conversation:
            active_conversation = repositories.create_conversation(db, customer.id)
        
        # Evaluar amenazas en el mensaje
        threat_result = threat_detection.analyze_message(message_body)
        threat_score = threat_result.get("score", 0)
        
        # Guardar el mensaje en la base de datos
        message = repositories.add_message(
            db=db,
            conversation_id=active_conversation.id,
            content=message_body,
            is_from_customer=True,
            suspicious_score=threat_score,
            ai_analysis=threat_result
        )
        
        # Si el mensaje es sospechoso (nivel alto), notificar
        if threat_score >= 0.8:
            logger.warning(f"Mensaje altamente sospechoso detectado: {from_number}, score: {threat_score}")
            
            # Notificar al administrador
            notification_content = (
                f"⚠️ ALERTA: Mensaje sospechoso\n"
                f"Número: {from_number}\n"
                f"Score: {threat_score}\n"
                f"Mensaje: {message_body}\n"
                f"Análisis: {json.dumps(threat_result, indent=2)}"
            )
            background_tasks.add_task(
                notification_service.send_alert,
                notification_content
            )
            
            # Enviar respuesta disuasiva
            response_text = (
                "AVISO IMPORTANTE: Esta conversación está siendo monitoreada. "
                "Si está realizando una amenaza o intento de extorsión, la información "
                "será enviada automáticamente a la Policía Nacional del Perú. Este "
                "número ya ha sido registrado en nuestra base de datos."
            )
            background_tasks.add_task(
                twilio_service.send_message,
                to=from_number,
                message=response_text
            )
            
            return JSONResponse(
                content={"status": "warning", "message": "Mensaje sospechoso detectado"},
                status_code=status.HTTP_200_OK
            )
        
        # Procesar el mensaje y obtener respuesta utilizando el motor de conversación
        bot_response = conversation.process_message(
            db=db,
            customer=customer,
            conversation=active_conversation,
            message_text=message_body,
            threat_analysis=threat_result
        )
        
        # Guardar la respuesta del bot en la base de datos
        bot_message = repositories.add_message(
            db=db,
            conversation_id=active_conversation.id,
            content=bot_response,
            is_from_customer=False,
            suspicious_score=0.0
        )
        
        # Enviar la respuesta al usuario
        background_tasks.add_task(
            twilio_service.send_message,
            to=from_number,
            message=bot_response
        )
        
        return JSONResponse(
            content={"status": "success", "message": "Mensaje procesado correctamente"},
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error procesando webhook de Twilio: {str(e)}")
        # En producción, no devuelvas el error específico para evitar fugas de información
        return JSONResponse(
            content={"status": "error", "message": "Error interno del servidor"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/payment_callback")
async def payment_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook para recibir callbacks de pasarelas de pago (Culqi, etc).
    
    Este endpoint maneja las notificaciones de pagos exitosos y actualiza 
    el estado de las órdenes correspondientes.
    """
    try:
        # Obtener payload completo
        payload = await request.json()
        logger.info(f"Callback de pago recibido: {json.dumps(payload)[:100]}...")
        
        # Extraer datos según pasarela (ejemplo para Culqi)
        payment_id = payload.get("id")
        order_id = payload.get("metadata", {}).get("order_id")
        status = payload.get("state") or payload.get("status")
        
        if not order_id or not payment_id:
            return JSONResponse(
                content={"status": "error", "message": "Información de orden incompleta"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar estado de la orden
        if status in ["pagado", "paid", "success", "completed"]:
            order = repositories.update_order_payment(
                db=db,
                order_id=int(order_id),
                payment_id=payment_id
            )
            
            if not order:
                logger.warning(f"Orden no encontrada para pago: {order_id}, payment_id: {payment_id}")
                return JSONResponse(
                    content={"status": "error", "message": "Orden no encontrada"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Notificar al cliente del pago exitoso
            customer = order.customer
            message = (
                f"¡Gracias por tu compra! Tu pago ha sido confirmado.\n"
                f"Número de orden: {order.id}\n"
                f"Monto total: S/{order.total_amount:.2f}\n\n"
                f"Pronto recibirás información sobre la entrega de tu pedido."
            )
            
            background_tasks.add_task(
                twilio_service.send_message,
                to=customer.phone_number,
                message=message
            )
            
            # Notificar al administrador
            notification_content = (
                f"✅ NUEVO PAGO CONFIRMADO\n"
                f"Orden: {order.id}\n"
                f"Cliente: {customer.name or customer.phone_number}\n"
                f"Monto: S/{order.total_amount:.2f}\n"
                f"ID Pago: {payment_id}"
            )
            background_tasks.add_task(
                notification_service.send_alert,
                notification_content
            )
        
        return JSONResponse(
            content={"status": "success", "message": "Callback procesado correctamente"},
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error procesando callback de pago: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": "Error interno del servidor"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )