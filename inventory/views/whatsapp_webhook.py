"""
Webhook para recibir respuestas de WhatsApp y procesarlas con IA
"""
import logging
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone

from inventory.models import PurchaseOrder
from inventory.services.purchase_order_ai_service import purchase_order_ai_service
from inventory.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """
    Webhook para recibir mensajes de WhatsApp
    """
    
    def get(self, request):
        """Verificación del webhook (Meta WhatsApp)"""
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        # Token de verificación para Meta WhatsApp
        VERIFY_TOKEN = "DATALENS_WEBHOOK_2025"
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("✅ Webhook de WhatsApp verificado exitosamente")
            return HttpResponse(challenge)
        else:
            logger.warning("❌ Token de verificación incorrecto")
            return HttpResponse('Forbidden', status=403)
    
    def post(self, request):
        """Procesar mensajes recibidos de WhatsApp"""
        try:
            data = json.loads(request.body)
            logger.info(f"📱 Webhook WhatsApp recibido: {json.dumps(data, indent=2)}")
            
            # Procesar diferentes tipos de webhooks
            if self._is_meta_webhook(data):
                return self._process_meta_webhook(data)
            elif self._is_twilio_webhook(data):
                return self._process_twilio_webhook(data)
            else:
                logger.warning("❓ Tipo de webhook no reconocido")
                return JsonResponse({'status': 'unknown_webhook'})
                
        except Exception as e:
            logger.error(f"❌ Error procesando webhook: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def _is_meta_webhook(self, data):
        """Detectar si es webhook de Meta WhatsApp"""
        return 'entry' in data and 'object' in data
    
    def _is_twilio_webhook(self, data):
        """Detectar si es webhook de Twilio"""
        return any(key.startswith('From') for key in data.keys())
    
    def _process_meta_webhook(self, data):
        """Procesar webhook de Meta WhatsApp Business"""
        try:
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        value = change.get('value', {})
                        
                        # Procesar mensajes recibidos
                        for message in value.get('messages', []):
                            self._process_incoming_message(
                                message_id=message.get('id'),
                                sender_phone=message.get('from'),
                                message_text=message.get('text', {}).get('body', ''),
                                message_type=message.get('type'),
                                timestamp=message.get('timestamp'),
                                webhook_type='meta',
                                image_data=message.get('image') if message.get('type') == 'image' else None
                            )
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Error procesando webhook Meta: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def _process_twilio_webhook(self, data):
        """Procesar webhook de Twilio WhatsApp"""
        try:
            sender_phone = data.get('From', '').replace('whatsapp:', '')
            message_text = data.get('Body', '')
            message_id = data.get('MessageSid')
            
            self._process_incoming_message(
                message_id=message_id,
                sender_phone=sender_phone,
                message_text=message_text,
                message_type='text',
                timestamp=None,
                webhook_type='twilio',
                image_data=None
            )
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Error procesando webhook Twilio: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def _process_incoming_message(self, message_id, sender_phone, message_text, message_type, timestamp, webhook_type, image_data=None):
        """
        Procesar mensaje entrante y buscar órdenes relacionadas
        """
        try:
            logger.info(f"📨 Mensaje recibido de {sender_phone}: {message_text} (tipo: {message_type})")
            
            # Buscar órdenes de compra pendientes para este número
            pending_orders = PurchaseOrder.objects.filter(
                supplier_whatsapp=sender_phone,
                status__in=['sent', 'confirmed'],
                whatsapp_sent=True
            ).order_by('-created_at')
            
            if not pending_orders.exists():
                logger.info(f"📋 No hay órdenes pendientes para {sender_phone}")
                return
            
            # Procesar la orden más reciente
            latest_order = pending_orders.first()
            
            # Manejar diferentes tipos de mensajes
            if message_type == 'image' and image_data:
                # Procesar foto de entrega
                self._process_delivery_photo(latest_order, image_data, sender_phone)
            else:
                # Procesar mensaje de texto
                self._process_text_message(latest_order, message_text, sender_phone)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
    
    def _process_text_message(self, purchase_order, message_text, sender_phone):
        """
        Procesar mensaje de texto del proveedor
        """
        try:
            # Analizar mensaje con IA
            analysis = purchase_order_ai_service.analyze_whatsapp_message(
                message_text=message_text,
                purchase_order=purchase_order,
                sender_phone=sender_phone
            )
            
            logger.info(f"🤖 Análisis IA: {json.dumps(analysis, indent=2)}")
            
            # Actualizar orden basada en análisis
            self._update_purchase_order_from_analysis(purchase_order, analysis, message_text)
            
            # Generar respuesta automática si es necesario
            if analysis.get('confidence', 0) > 0.8:
                follow_up = purchase_order_ai_service.generate_follow_up_message(purchase_order, analysis)
                self._send_automatic_response(sender_phone, follow_up, purchase_order.company)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje de texto: {str(e)}")
    
    def _process_delivery_photo(self, purchase_order, image_data, sender_phone):
        """
        Procesar foto de entrega del proveedor
        """
        try:
            logger.info(f"📸 Procesando foto de entrega para orden {purchase_order.order_number}")
            
            # Obtener URL de la imagen (Meta WhatsApp)
            image_url = self._get_image_url(image_data)
            
            if not image_url:
                logger.error("❌ No se pudo obtener URL de la imagen")
                return
            
            # Analizar imagen con IA
            photo_analysis = purchase_order_ai_service.analyze_delivery_photo(
                image_url=image_url,
                purchase_order=purchase_order
            )
            
            logger.info(f"📸🤖 Análisis de foto: {json.dumps(photo_analysis, indent=2)}")
            
            # Actualizar orden con análisis de foto
            purchase_order.delivery_photo_url = image_url
            purchase_order.delivery_photo_analysis = photo_analysis
            
            # Marcar como entregado si la foto es válida
            if photo_analysis.get('is_valid_delivery') and photo_analysis.get('confidence', 0) > 0.7:
                purchase_order.status = 'delivered'
                purchase_order.delivered_at = timezone.now()
                logger.info(f"✅ Orden {purchase_order.order_number} marcada como ENTREGADA")
                
                # Enviar confirmación automática
                confirmation_msg = f"""
✅ *Entrega Confirmada*

Hemos recibido la foto de entrega para la orden {purchase_order.order_number}.

📋 *Verificación IA:*
• Estado: {photo_analysis.get('verification_summary')}
• Calidad: {photo_analysis.get('delivery_quality')}
• Confianza: {photo_analysis.get('confidence', 0):.0%}

¡Gracias por su servicio!
"""
                self._send_automatic_response(sender_phone, confirmation_msg, purchase_order.company)
            
            purchase_order.save()
            
            # Crear alerta de entrega
            self._create_delivery_notification(purchase_order, photo_analysis)
            
        except Exception as e:
            logger.error(f"Error procesando foto de entrega: {str(e)}")
    
    def _get_image_url(self, image_data):
        """
        Obtener URL de imagen desde datos de WhatsApp
        """
        try:
            # Para Meta WhatsApp Business API
            image_id = image_data.get('id')
            if image_id:
                # Aquí necesitarías implementar la lógica para obtener la URL
                # usando el Graph API de Meta con el image_id
                # Por ahora, retornamos None para evitar errores
                logger.warning(f"⚠️ Implementar descarga de imagen: {image_id}")
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo URL de imagen: {str(e)}")
            return None
    
    def _create_delivery_notification(self, purchase_order, photo_analysis):
        """
        Crear notificación de entrega
        """
        try:
            from alerts.models import Alert
            
            is_valid = photo_analysis.get('is_valid_delivery', False)
            confidence = photo_analysis.get('confidence', 0)
            
            Alert.objects.create(
                company=purchase_order.company,
                product=purchase_order.product,
                title=f"📸 {'✅ Entrega Confirmada' if is_valid else '⚠️ Foto de Entrega Recibida'}: {purchase_order.order_number}",
                message=f"""
El proveedor {purchase_order.supplier.name if purchase_order.supplier else 'N/A'} ha enviado una foto de entrega:

📸 Análisis de Imagen:
• Entrega válida: {'Sí' if is_valid else 'No'}
• Confianza: {confidence:.0%}
• Calidad: {photo_analysis.get('delivery_quality', 'N/A')}
• Productos detectados: {', '.join(photo_analysis.get('products_detected', []))}

📋 Orden: {purchase_order.order_number}
🏷️ Producto: {purchase_order.product.name}
💰 Total: S/ {purchase_order.total_amount}

{photo_analysis.get('verification_summary', '')}
""",
                severity='low' if is_valid else 'medium',
                status='active',
                source='whatsapp_delivery_photo',
                context_data={
                    'purchase_order_id': purchase_order.id,
                    'photo_analysis': photo_analysis,
                    'delivery_confirmed': is_valid
                }
            )
            
        except Exception as e:
            logger.error(f"Error creando notificación de entrega: {str(e)}")
    
    def _update_purchase_order_from_analysis(self, purchase_order, analysis, original_message):
        """
        Actualizar orden de compra basada en análisis de IA
        """
        try:
            action = analysis.get('action')
            confidence = analysis.get('confidence', 0)
            
            # Actualizar respuesta del proveedor
            purchase_order.supplier_response = original_message
            purchase_order.updated_at = timezone.now()
            
            # Procesar según la acción detectada
            if action == 'confirmed' and confidence > 0.7:
                purchase_order.status = 'confirmed'
                purchase_order.confirmed_at = timezone.now()
                logger.info(f"✅ Orden {purchase_order.order_number} CONFIRMADA por proveedor")
                
            elif action == 'rejected' and confidence > 0.7:
                purchase_order.status = 'rejected'
                purchase_order.rejected_at = timezone.now()
                logger.info(f"❌ Orden {purchase_order.order_number} RECHAZADA por proveedor")
                
            elif action == 'negotiating':
                purchase_order.status = 'negotiating'
                # Guardar precio propuesto si existe
                if analysis.get('price_proposed'):
                    purchase_order.negotiated_price = analysis.get('price_proposed')
                logger.info(f"💬 Orden {purchase_order.order_number} en NEGOCIACIÓN")
            
            # Guardar análisis en campo JSON
            purchase_order.ai_analysis = analysis
            purchase_order.save()
            
            # Crear notificación interna para el equipo
            self._create_internal_notification(purchase_order, analysis)
            
        except Exception as e:
            logger.error(f"Error actualizando orden: {str(e)}")
    
    def _create_internal_notification(self, purchase_order, analysis):
        """
        Crear notificación interna para el equipo sobre la respuesta del proveedor
        """
        try:
            from alerts.models import Alert
            
            action = analysis.get('action', 'unclear')
            confidence = analysis.get('confidence', 0)
            
            titles = {
                'confirmed': f'✅ Orden Confirmada: {purchase_order.order_number}',
                'rejected': f'❌ Orden Rechazada: {purchase_order.order_number}',
                'negotiating': f'💬 Negociación: {purchase_order.order_number}',
                'unclear': f'❓ Respuesta Poco Clara: {purchase_order.order_number}'
            }
            
            Alert.objects.create(
                company=purchase_order.company,
                product=purchase_order.product,
                title=titles.get(action, titles['unclear']),
                message=f"""
El proveedor {purchase_order.supplier.name if purchase_order.supplier else 'N/A'} ha respondido:

📱 Mensaje: "{purchase_order.supplier_response}"
🤖 IA Detectó: {action} (confianza: {confidence:.0%})
📋 Resumen: {analysis.get('summary', 'N/A')}

Orden: {purchase_order.order_number}
Producto: {purchase_order.product.name}
Total: S/ {purchase_order.total_amount}
""",
                severity='medium' if action in ['confirmed', 'rejected'] else 'high',
                status='active',
                source='whatsapp_webhook',
                context_data={
                    'purchase_order_id': purchase_order.id,
                    'ai_analysis': analysis,
                    'webhook_processed': True
                }
            )
            
        except Exception as e:
            logger.error(f"Error creando notificación: {str(e)}")
    
    def _send_automatic_response(self, recipient_phone, message, company):
        """
        Enviar respuesta automática al proveedor
        """
        try:
            whatsapp_service = WhatsAppService(company=company)
            
            result = whatsapp_service.send_message(
                recipient_number=recipient_phone,
                message=message
            )
            
            if result.get('success'):
                logger.info(f"📱✅ Respuesta automática enviada a {recipient_phone}")
            else:
                logger.error(f"📱❌ Error enviando respuesta: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error enviando respuesta automática: {str(e)}")


# Para Twilio webhook (formato diferente)
@csrf_exempt
@require_http_methods(["POST"])
def twilio_whatsapp_webhook(request):
    """Webhook específico para Twilio (compatibilidad)"""
    webhook_view = WhatsAppWebhookView()
    return webhook_view.post(request)
