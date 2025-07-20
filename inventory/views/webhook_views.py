"""
Vistas para webhooks y API de WhatsApp
"""
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from inventory.models import PurchaseOrder
from inventory.services.whatsapp_service import whatsapp_service
from inventory.serializers.purchase_order_serializers import PurchaseOrderSerializer

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def meta_whatsapp_webhook(request):
    """
    Webhook para Meta WhatsApp Business Cloud API
    """
    if request.method == "GET":
        # Verificación del webhook
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        
        verify_token = getattr(settings, 'META_WHATSAPP_VERIFY_TOKEN', 'datalens_webhook_token')
        
        if mode and token:
            if mode == "subscribe" and token == verify_token:
                logger.info("✅ Webhook Meta WhatsApp verificado")
                return HttpResponse(challenge, content_type="text/plain")
            else:
                logger.warning("❌ Token de verificación WhatsApp incorrecto")
                return HttpResponse("Forbidden", status=403)
        
        return HttpResponse("Bad Request", status=400)
    
    elif request.method == "POST":
        # Procesar mensaje entrante
        try:
            body = json.loads(request.body.decode('utf-8'))
            
            # Log del webhook recibido
            logger.info(f"📱 Webhook Meta WhatsApp recibido: {json.dumps(body, indent=2)}")
            
            # Procesar entrada del webhook
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    # Procesar mensajes
                    if "messages" in value:
                        for message in value["messages"]:
                            _process_incoming_whatsapp_message(message, value)
                    
                    # Procesar estados de mensajes
                    if "statuses" in value:
                        for status_update in value["statuses"]:
                            _process_whatsapp_status_update(status_update)
            
            return JsonResponse({"status": "success"})
            
        except Exception as e:
            logger.error(f"Error procesando webhook Meta WhatsApp: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def twilio_whatsapp_webhook(request):
    """
    Webhook para Twilio WhatsApp API
    """
    try:
        # Twilio envía datos como form-encoded
        from_number = request.POST.get('From', '')
        body_text = request.POST.get('Body', '')
        message_sid = request.POST.get('MessageSid', '')
        
        logger.info(f"📱 Webhook Twilio WhatsApp: {from_number} -> {body_text}")
        
        # Procesar mensaje
        if from_number and body_text:
            # Limpiar número (quitar whatsapp: prefix)
            phone_number = from_number.replace('whatsapp:', '')
            
            # Generar respuesta automática
            response = whatsapp_service.send_webhook_response(phone_number, body_text)
            
            if response['success']:
                logger.info(f"✅ Respuesta automática enviada a {phone_number}")
            else:
                logger.error(f"❌ Error enviando respuesta: {response.get('error')}")
        
        # Twilio espera respuesta TwiML (opcional)
        return HttpResponse("""<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>""", content_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error procesando webhook Twilio: {str(e)}")
        return HttpResponse("Error", status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_purchase_order_whatsapp(request):
    """
    API endpoint para enviar orden de compra por WhatsApp
    POST /api/whatsapp/send-order/
    
    Body:
    {
        "purchase_order_id": 123,
        "recipient_number": "+51999999999"  // opcional
    }
    """
    try:
        purchase_order_id = request.data.get('purchase_order_id')
        recipient_number = request.data.get('recipient_number')
        
        if not purchase_order_id:
            return Response(
                {'error': 'purchase_order_id es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener orden de compra
        try:
            purchase_order = PurchaseOrder.objects.get(
                id=purchase_order_id,
                company=request.user.company
            )
        except PurchaseOrder.DoesNotExist:
            return Response(
                {'error': 'Orden de compra no encontrada'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Enviar WhatsApp
        result = whatsapp_service.send_purchase_order_message(
            purchase_order, 
            recipient_number
        )
        
        if result['success']:
            # Serializar orden actualizada
            serializer = PurchaseOrderSerializer(purchase_order)
            
            return Response({
                'success': True,
                'message': 'WhatsApp enviado exitosamente',
                'message_id': result.get('message_id'),
                'service': result.get('service'),
                'purchase_order': serializer.data
            })
        else:
            return Response(
                {'error': result.get('error', 'Error desconocido')}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error en send_purchase_order_whatsapp: {str(e)}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def whatsapp_message_status(request, message_id):
    """
    Obtener estado de un mensaje WhatsApp
    GET /api/whatsapp/status/{message_id}/
    """
    try:
        # Buscar orden por message_id
        purchase_order = PurchaseOrder.objects.filter(
            whatsapp_message_id=message_id,
            company=request.user.company
        ).first()
        
        if not purchase_order:
            return Response(
                {'error': 'Mensaje no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'message_id': message_id,
            'purchase_order_id': purchase_order.id,
            'order_number': purchase_order.order_number,
            'whatsapp_sent': purchase_order.whatsapp_sent,
            'whatsapp_sent_at': purchase_order.whatsapp_sent_at,
            'supplier_whatsapp': purchase_order.supplier_whatsapp,
            'status': purchase_order.status
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado WhatsApp: {str(e)}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _process_incoming_whatsapp_message(message, value):
    """Procesar mensaje WhatsApp entrante"""
    try:
        phone_number = message.get("from", "")
        message_text = ""
        message_type = message.get("type", "")
        
        # Extraer texto según el tipo de mensaje
        if message_type == "text":
            message_text = message.get("text", {}).get("body", "")
        elif message_type == "interactive":
            # Manejo de botones interactivos (futuro)
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                message_text = interactive.get("button_reply", {}).get("title", "")
        
        logger.info(f"📱 Mensaje recibido de {phone_number}: {message_text}")
        
        # Buscar si este número corresponde a algún proveedor
        from inventory.models import Supplier
        supplier = Supplier.objects.filter(
            whatsapp_number=phone_number,
            whatsapp_enabled=True
        ).first()
        
        if supplier:
            logger.info(f"📋 Mensaje de proveedor: {supplier.name}")
            
            # Buscar órdenes pendientes de este proveedor
            pending_orders = PurchaseOrder.objects.filter(
                supplier=supplier,
                status__in=['sent', 'draft'],
                whatsapp_sent=True
            ).order_by('-created_at')[:5]  # Últimas 5 órdenes
            
            if pending_orders.exists():
                logger.info(f"📦 {pending_orders.count()} órdenes pendientes encontradas")
                
                # Procesar respuesta del proveedor
                _process_supplier_response(supplier, message_text, pending_orders)
        
        # Enviar respuesta automática
        response = whatsapp_service.send_webhook_response(phone_number, message_text)
        
        if response['success']:
            logger.info(f"✅ Respuesta automática enviada a {phone_number}")
        
    except Exception as e:
        logger.error(f"Error procesando mensaje WhatsApp: {str(e)}")


def _process_whatsapp_status_update(status_update):
    """Procesar actualización de estado de mensaje WhatsApp"""
    try:
        message_id = status_update.get("id", "")
        status_value = status_update.get("status", "")
        timestamp = status_update.get("timestamp", "")
        
        logger.info(f"📱 Estado WhatsApp actualizado: {message_id} -> {status_value}")
        
        # Buscar orden por message_id
        purchase_order = PurchaseOrder.objects.filter(
            whatsapp_message_id=message_id
        ).first()
        
        if purchase_order:
            # Actualizar estado según el valor recibido
            if status_value == "delivered":
                logger.info(f"✅ WhatsApp entregado: {purchase_order.order_number}")
            elif status_value == "read":
                logger.info(f"👁️ WhatsApp leído: {purchase_order.order_number}")
            elif status_value == "failed":
                logger.warning(f"❌ WhatsApp falló: {purchase_order.order_number}")
        
    except Exception as e:
        logger.error(f"Error procesando estado WhatsApp: {str(e)}")


def _process_supplier_response(supplier, message_text, pending_orders):
    """Procesar respuesta del proveedor"""
    try:
        message_lower = message_text.lower().strip()
        
        # Detectar confirmaciones
        if any(word in message_lower for word in ['confirmado', 'confirmo', 'disponible', 'ok', 'sí', 'si']):
            # Marcar la orden más reciente como confirmada
            latest_order = pending_orders.first()
            if latest_order:
                latest_order.status = 'confirmed'
                latest_order.supplier_response = f"Confirmado via WhatsApp: {message_text}"
                latest_order.save()
                
                logger.info(f"✅ Orden confirmada: {latest_order.order_number}")
        
        # Detectar rechazos
        elif any(word in message_lower for word in ['no disponible', 'agotado', 'no tengo', 'sin stock']):
            latest_order = pending_orders.first()
            if latest_order:
                latest_order.status = 'cancelled'
                latest_order.supplier_response = f"Rechazado via WhatsApp: {message_text}"
                latest_order.save()
                
                logger.info(f"❌ Orden rechazada: {latest_order.order_number}")
        
        # Guardar respuesta genérica
        else:
            latest_order = pending_orders.first()
            if latest_order:
                current_response = latest_order.supplier_response or ""
                latest_order.supplier_response = f"{current_response}\nWhatsApp: {message_text}".strip()
                latest_order.save()
                
                logger.info(f"💬 Respuesta guardada: {latest_order.order_number}")
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de proveedor: {str(e)}")
