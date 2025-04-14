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
from app.config import TWILIO_ACCOUNT_SID, APP_ENV
from app.db.models import ConversationStatus  # Importando ConversationStatus
from app.utils.whatsapp import update_message_received, update_message_sent  # Importando update_message_received y update_message_sent
from app.security.access_control import is_whitelisted  # Importando is_whitelisted

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
    
    # Actualizar el estado de conexión cuando se recibe un mensaje
    update_message_received()
    
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
        
        # En desarrollo, permitimos solicitudes sin SID para facilitar pruebas
        if APP_ENV == "production" and account_sid != TWILIO_ACCOUNT_SID:
            logger.warning(f"Intento de webhook con SID inválido: {account_sid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autorizado"
            )
        
        # Registrar todos los datos del formulario para depuración
        logger.info(f"Datos del formulario recibidos: {dict(form_data)}")
        
        # Verificar si el número está en la lista negra o en la whitelist
        phone_without_prefix = from_number.replace("whatsapp:", "")
        if is_whitelisted(phone_without_prefix):
            logger.info(f"Número en whitelist, permitiendo mensaje: {from_number}")
            # Permitir que el mensaje continúe
        elif repositories.is_phone_blacklisted(db, from_number):
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
        
        # Si el mensaje es sospechoso (nivel alto), notificar y posiblemente bloquear
        if threat_score >= 0.8:
            logger.warning(f"Mensaje altamente sospechoso detectado: {from_number}, score: {threat_score}")
            
            # Notificar al administrador utilizando el servicio mejorado
            customer_info = {
                "name": customer.name or "No registrado",
                "dni": customer.dni or "No registrado",
                "created_at": customer.created_at.isoformat() if customer.created_at else "Desconocido",
                "id": customer.id
            }
            
            notification_service.send_threat_alert(
                phone_number=from_number,
                message_content=message_body,
                threat_analysis=threat_result,
                customer_info=customer_info
            )
            
            # Si el nivel es crítico, bloqueamos automáticamente
            if threat_result.get("threat_level") == "alto":
                # Añadir a la lista negra
                from app.security import blacklist
                reason = f"Mensaje de amenaza automáticamente detectado. Score: {threat_score}"
                blacklist.add_to_blacklist(
                    db=db, 
                    phone_number=from_number, 
                    reason=reason,
                    source="automatic"
                )
                
                # Bloquear cliente
                repositories.block_customer(db, customer.id, reason=reason)
                
                # Marcar conversación como bloqueada
                repositories.update_conversation_status(
                    db=db,
                    conversation_id=active_conversation.id,
                    status=ConversationStatus.BLOCKED,
                    suspicious_score=threat_score
                )
                
                logger.warning(f"Cliente bloqueado automáticamente: {from_number}")
                
                # Enviar mensaje de bloqueo
                response_text = (
                    "⚠️ AVISO IMPORTANTE: Esta conversación ha sido suspendida y reportada a las autoridades. "
                    "Si está realizando una amenaza o intento de extorsión, sepa que la información "
                    "ya ha sido enviada a la Policía Nacional. Este "
                    "número ha sido registrado en nuestra base de datos y bloqueado permanentemente."
                )
                background_tasks.add_task(
                    twilio_service.send_message,
                    to=from_number,
                    message=response_text
                )
                
                return JSONResponse(
                    content={"status": "blocked", "message": "Cliente bloqueado por amenazas"},
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            # Si es sospechoso pero no crítico, enviamos advertencia pero continuamos
            response_text = (
                "AVISO IMPORTANTE: Esta conversación está siendo monitoreada. "
                "Todas las comunicaciones son registradas y analizadas. "
                "Este canal colabora con las autoridades en casos de extorsión o amenazas."
            )
            background_tasks.add_task(
                twilio_service.send_message,
                to=from_number,
                message=response_text
            )
            
            # Marcar conversación como sospechosa
            repositories.update_conversation_status(
                db=db,
                conversation_id=active_conversation.id,
                status=ConversationStatus.SUSPICIOUS,
                suspicious_score=threat_score
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