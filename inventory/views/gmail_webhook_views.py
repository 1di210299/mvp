"""
Vistas para Gmail OAuth2 y Webhooks
Maneja la autenticación y recepción de notificaciones de Gmail
"""
import json
import logging
from typing import Dict, Any

from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.services.gmail_oauth_service import gmail_oauth_service
from inventory.services.pubsub_service import pubsub_service
from inventory.services.email_tracking_service import EmailTrackingService

logger = logging.getLogger(__name__)


class GmailOAuthView(APIView):
    """
    Vista para manejar OAuth2 con Gmail
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Iniciar proceso de autorización OAuth2"""
        try:
            if not gmail_oauth_service.is_available():
                return Response({
                    'error': 'Gmail OAuth no está configurado correctamente',
                    'details': {
                        'client_id_configured': bool(settings.GMAIL_CLIENT_ID),
                        'client_secret_configured': bool(settings.GMAIL_CLIENT_SECRET),
                        'redirect_uri': settings.GMAIL_REDIRECT_URI
                    }
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Verificar si ya está autenticado
            if gmail_oauth_service.is_authenticated():
                watch_status = gmail_oauth_service.get_watch_status()
                return Response({
                    'authenticated': True,
                    'watch_status': watch_status,
                    'message': 'Ya está autenticado con Gmail'
                })
            
            # Generar URL de autorización
            auth_url, state = gmail_oauth_service.get_authorization_url(
                user_id=str(request.user.id)
            )
            
            if not auth_url:
                return Response({
                    'error': 'No se pudo generar URL de autorización'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'authorization_url': auth_url,
                'state': state,
                'message': 'Visite la URL para autorizar la aplicación'
            })
            
        except Exception as e:
            logger.error(f"Error en Gmail OAuth: {e}")
            return Response({
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["GET"])
def gmail_oauth_callback(request):
    """
    Callback de OAuth2 de Gmail
    """
    try:
        # Obtener parámetros del callback
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        if error:
            logger.error(f"Error en OAuth callback: {error}")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=oauth_error&message={error}")
        
        if not code or not state:
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=missing_parameters")
        
        # Procesar callback
        result = gmail_oauth_service.handle_oauth_callback(code, state)
        
        if result['success']:
            return HttpResponseRedirect(
                f"{settings.FRONTEND_URL}/?success=gmail_connected&webhook={result.get('webhook_configured', False)}"
            )
        else:
            return HttpResponseRedirect(
                f"{settings.FRONTEND_URL}/?error=oauth_failed&message={result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Error en OAuth callback: {e}")
        return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=callback_error")


class GmailWebhookView(APIView):
    """
    Vista para manejar webhooks de Gmail via Pub/Sub
    """
    permission_classes = []  # Sin autenticación para webhooks
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Recibir notificación de webhook de Gmail"""
        try:
            # Verificar que el request venga de Google Pub/Sub
            if not self._verify_pubsub_request(request):
                logger.warning("🚨 Webhook request no válido (no es de Pub/Sub)")
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            
            # Parsear mensaje de Pub/Sub
            message_data = pubsub_service.parse_pubsub_message(request.data)
            
            if not message_data:
                logger.error("❌ No se pudo parsear mensaje de Pub/Sub")
                return Response(status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"📨 Webhook recibido: {message_data['message_id']}")
            
            # Procesar notificación de Gmail
            result = self._process_gmail_notification(message_data)
            
            if result['success']:
                return Response({'status': 'processed'})
            else:
                logger.error(f"❌ Error procesando notificación: {result.get('error')}")
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"❌ Error en webhook: {e}")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _verify_pubsub_request(self, request) -> bool:
        """Verificar que el request venga de Google Pub/Sub"""
        try:
            # Verificar headers básicos
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if 'Google-Cloud-Pub-Sub' not in user_agent:
                return False
            
            # Verificar que tenga estructura de mensaje Pub/Sub
            if 'message' not in request.data:
                return False
            
            # Aquí podrías agregar verificación adicional como JWT tokens
            # Por simplicidad, solo verificamos estructura básica
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando request Pub/Sub: {e}")
            return False
    
    def _process_gmail_notification(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar notificación de Gmail"""
        try:
            # Extraer datos de la notificación
            gmail_data = message_data.get('data', {})
            history_id = gmail_data.get('historyId')
            
            if not history_id:
                return {'success': False, 'error': 'No history_id en notificación'}
            
            logger.info(f"📧 Procesando cambios Gmail hasta history_id: {history_id}")
            
            # Procesar cambios usando EmailTrackingService
            email_tracking = EmailTrackingService()
            result = email_tracking.process_gmail_webhook_notification(gmail_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error procesando notificación Gmail: {e}")
            return {'success': False, 'error': str(e)}


class GmailWebhookStatusView(APIView):
    """
    Vista para consultar estado del webhook de Gmail
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener estado del webhook"""
        try:
            # Estado de autenticación
            auth_status = {
                'authenticated': gmail_oauth_service.is_authenticated(),
                'oauth_available': gmail_oauth_service.is_available()
            }
            
            # Estado del watch
            watch_status = gmail_oauth_service.get_watch_status()
            
            # Estado de Pub/Sub
            pubsub_status = {
                'available': pubsub_service.is_available(),
                'project_id': settings.GOOGLE_CLOUD_PROJECT_ID,
                'topic_name': settings.PUBSUB_TOPIC_NAME,
                'subscription_name': settings.PUBSUB_SUBSCRIPTION_NAME
            }
            
            return Response({
                'auth_status': auth_status,
                'watch_status': watch_status,
                'pubsub_status': pubsub_status,
                'webhook_url': settings.PUBSUB_WEBHOOK_URL
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estado webhook: {e}")
            return Response({
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Configurar o reconfigurar webhook"""
        try:
            action = request.data.get('action', 'start')
            
            if action == 'start':
                result = gmail_oauth_service.setup_gmail_webhook()
            elif action == 'stop':
                result = gmail_oauth_service.stop_gmail_webhook()
            else:
                return Response({
                    'error': 'Acción no válida. Use "start" o "stop"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error configurando webhook: {e}")
            return Response({
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_gmail_webhook(request):
    """
    Endpoint para probar webhook de Gmail (desarrollo)
    """
    try:
        # Generar mensaje de prueba
        test_message = {
            'historyId': '12345',
            'emailAddress': 'test@example.com'
        }
        
        # Publicar mensaje de prueba en Pub/Sub
        message_id = pubsub_service.publish_message(test_message)
        
        if message_id:
            return Response({
                'success': True,
                'message_id': message_id,
                'message': 'Mensaje de prueba publicado en Pub/Sub'
            })
        else:
            return Response({
                'success': False,
                'error': 'No se pudo publicar mensaje de prueba'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error en test webhook: {e}")
        return Response({
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
