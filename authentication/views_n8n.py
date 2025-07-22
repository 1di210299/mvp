"""
Vistas para el flujo N8N de onboarding de tenants
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
import logging

from .models import TenantConfig, UsageLog
from .auth import TenantJWTAuthentication
from .serializers import (
    TenantConfigSerializer, TenantCreateSerializer, UsageLogSerializer,
    WhatsAppSendSerializer, EmailSendSerializer, UsageReportSerializer,
    WebhookWhatsAppSerializer
)
from .services import (
    TenantOnboardingService, WhatsAppService, EmailService, 
    UsageReportService
)

logger = logging.getLogger(__name__)


class TenantCreateAPIView(APIView):
    """API para crear nuevos tenants"""
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=TenantCreateSerializer,
        responses={201: TenantConfigSerializer, 400: 'Bad Request'}
    )
    def post(self, request):
        """Crear un nuevo tenant"""
        serializer = TenantCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Usar el servicio para crear el tenant
            result = TenantOnboardingService.create_tenant(
                name=serializer.validated_data['name'],
                domain=serializer.validated_data['domain'],
                email_address=serializer.validated_data['email_address'],
                whatsapp_number=serializer.validated_data.get('whatsapp_number')
            )
            
            if result['success']:
                # Obtener el tenant creado
                tenant = TenantConfig.objects.get(tenant_id=result['tenant_id'])
                response_serializer = TenantConfigSerializer(tenant)
                
                return Response({
                    'success': True,
                    'tenant_id': result['tenant_id'],
                    'message': result['message'],
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TenantDetailAPIView(generics.RetrieveUpdateAPIView):
    """API para obtener y actualizar detalles de tenant"""
    queryset = TenantConfig.objects.all()
    serializer_class = TenantConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'tenant_id'


class TenantListAPIView(generics.ListAPIView):
    """API para listar tenants"""
    queryset = TenantConfig.objects.all()
    serializer_class = TenantConfigSerializer
    permission_classes = [permissions.IsAuthenticated]


class WhatsAppSendAPIView(APIView):
    """API para enviar mensajes de WhatsApp"""
    authentication_classes = [TenantJWTAuthentication]
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        request=WhatsAppSendSerializer,
        responses={200: 'Message sent', 400: 'Bad Request'}
    )
    def post(self, request, tenant_id):
        """Enviar mensaje de WhatsApp"""
        serializer = WhatsAppSendSerializer(data=request.data)
        
        if serializer.is_valid():
            result = WhatsAppService.send_text(
                tenant_id=tenant_id,
                to=serializer.validated_data['to'],
                body=serializer.validated_data['body']
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message_id': result.get('message_id'),
                    'log_id': result.get('log_id')
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['error'],
                    'log_id': result.get('log_id')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EmailSendAPIView(APIView):
    """API para enviar emails"""
    authentication_classes = [TenantJWTAuthentication]
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        request=EmailSendSerializer,
        responses={200: 'Email sent', 400: 'Bad Request'}
    )
    def post(self, request, tenant_id):
        """Enviar email"""
        serializer = EmailSendSerializer(data=request.data)
        
        if serializer.is_valid():
            result = EmailService.send_email(
                tenant_id=tenant_id,
                to=serializer.validated_data['to'],
                subject=serializer.validated_data['subject'],
                body=serializer.validated_data['body'],
                attachments=serializer.validated_data.get('attachments')
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': result['message'],
                    'log_id': result.get('log_id')
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['error'],
                    'log_id': result.get('log_id')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TenantUsageAPIView(APIView):
    """API para obtener reportes de uso de tenant"""
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        parameters=[UsageReportSerializer],
        responses={200: 'Usage report'}
    )
    def get(self, request, tenant_id):
        """Obtener reporte de uso"""
        serializer = UsageReportSerializer(data=request.query_params)
        
        if serializer.is_valid():
            result = UsageReportService.get_tenant_usage(
                tenant_id=tenant_id,
                start_date=serializer.validated_data.get('start_date'),
                end_date=serializer.validated_data.get('end_date')
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UsageLogListAPIView(generics.ListAPIView):
    """API para listar logs de uso"""
    serializer_class = UsageLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tenant_id = self.kwargs.get('tenant_id')
        queryset = UsageLog.objects.filter(tenant__tenant_id=tenant_id)
        
        # Filtros opcionales
        channel = self.request.query_params.get('channel')
        status_filter = self.request.query_params.get('status')
        
        if channel:
            queryset = queryset.filter(channel=channel)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-timestamp')


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookAPIView(APIView):
    """API para recibir webhooks de WhatsApp"""
    permission_classes = []  # Webhooks no requieren autenticación JWT
    
    def get(self, request):
        """Verificación del webhook por parte de Meta"""
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        # Verificar token (configurar en settings)
        verify_token = "mi_webhook_token_secreto"  # TODO: Mover a settings
        
        if mode == 'subscribe' and token == verify_token:
            logger.info("Webhook verificado exitosamente")
            return Response(challenge, content_type='text/plain')
        else:
            logger.warning(f"Verificación de webhook fallida: mode={mode}, token={token}")
            return Response('Forbidden', status=status.HTTP_403_FORBIDDEN)
    
    @extend_schema(
        request=WebhookWhatsAppSerializer,
        responses={200: 'Webhook processed'}
    )
    def post(self, request):
        """Procesar webhook de WhatsApp"""
        serializer = WebhookWhatsAppSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Procesar cada entrada del webhook
                for entry in serializer.validated_data['entry']:
                    self.process_webhook_entry(entry)
                
                return Response({'status': 'ok'}, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Error procesando webhook: {str(e)}")
                return Response({
                    'error': 'Error interno del servidor'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def process_webhook_entry(self, entry):
        """Procesar una entrada del webhook"""
        try:
            changes = entry.get('changes', [])
            
            for change in changes:
                field = change.get('field')
                value = change.get('value', {})
                
                if field == 'messages':
                    # Mensaje recibido
                    messages = value.get('messages', [])
                    for message in messages:
                        self.process_incoming_message(message, value)
                
                elif field == 'message_status':
                    # Estado del mensaje
                    statuses = value.get('statuses', [])
                    for status_update in statuses:
                        self.process_message_status(status_update, value)
                        
        except Exception as e:
            logger.error(f"Error procesando entrada del webhook: {str(e)}")
    
    def process_incoming_message(self, message, value):
        """Procesar mensaje entrante"""
        try:
            from_number = message.get('from')
            message_id = message.get('id')
            timestamp = message.get('timestamp')
            message_type = message.get('type')
            
            # Encontrar tenant basado en el número de teléfono del webhook
            phone_number_id = value.get('metadata', {}).get('phone_number_id')
            
            try:
                tenant = TenantConfig.objects.get(phone_number_id=phone_number_id)
                
                # Registrar mensaje entrante
                UsageLog.objects.create(
                    tenant=tenant,
                    channel='whatsapp',
                    action='message_received',
                    status='success',
                    details={
                        'from': from_number,
                        'message_id': message_id,
                        'type': message_type,
                        'timestamp': timestamp,
                        'content': message.get('text', {}).get('body', '') if message_type == 'text' else f"[{message_type}]"
                    }
                )
                
                logger.info(f"Mensaje procesado para tenant {tenant.name}: {message_id}")
                
            except TenantConfig.DoesNotExist:
                logger.warning(f"Tenant no encontrado para phone_number_id: {phone_number_id}")
                
        except Exception as e:
            logger.error(f"Error procesando mensaje entrante: {str(e)}")
    
    def process_message_status(self, status_update, value):
        """Procesar actualización de estado de mensaje"""
        try:
            message_id = status_update.get('id')
            status_value = status_update.get('status')
            timestamp = status_update.get('timestamp')
            
            # Encontrar tenant
            phone_number_id = value.get('metadata', {}).get('phone_number_id')
            
            try:
                tenant = TenantConfig.objects.get(phone_number_id=phone_number_id)
                
                # Registrar actualización de estado
                UsageLog.objects.create(
                    tenant=tenant,
                    channel='whatsapp',
                    action='message_status_update',
                    status='success',
                    details={
                        'message_id': message_id,
                        'status': status_value,
                        'timestamp': timestamp
                    }
                )
                
                logger.info(f"Estado actualizado para tenant {tenant.name}: {message_id} -> {status_value}")
                
            except TenantConfig.DoesNotExist:
                logger.warning(f"Tenant no encontrado para phone_number_id: {phone_number_id}")
                
        except Exception as e:
            logger.error(f"Error procesando estado de mensaje: {str(e)}")


class DomainVerificationAPIView(APIView):
    """API para verificar dominio y configurar email"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tenant_id):
        """Iniciar verificación de dominio"""
        result = TenantOnboardingService.verify_domain_and_email(tenant_id)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class WhatsAppSetupAPIView(APIView):
    """API para configurar WhatsApp Business"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tenant_id):
        """Configurar WhatsApp Business para tenant"""
        whatsapp_number = request.data.get('whatsapp_number')
        
        if not whatsapp_number:
            return Response({
                'success': False,
                'error': 'whatsapp_number es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = WhatsAppService.setup_whatsapp_business(tenant_id, whatsapp_number)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
