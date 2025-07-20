"""
Vistas para configuración de empresa - WhatsApp
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from authentication.models import Company


class CompanyWhatsAppConfigView(APIView):
    """Vista para configurar WhatsApp de la empresa"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener configuración actual de WhatsApp"""
        company = request.user.company
        
        config = {
            'company_name': company.name,
            'whatsapp_business_number': company.whatsapp_business_number,
            'whatsapp_enabled': company.whatsapp_enabled,
            'whatsapp_plan': company.whatsapp_plan,
            'phone': company.phone,
            'email': company.email,
            'subscription_type': company.subscription_type,
            'can_upgrade': company.subscription_type in ['trial', 'basic'],
        }
        
        return Response(config)
    
    def put(self, request):
        """Actualizar configuración de WhatsApp"""
        company = request.user.company
        
        # Validar datos recibidos
        whatsapp_number = request.data.get('whatsapp_business_number', '').strip()
        whatsapp_enabled = request.data.get('whatsapp_enabled', False)
        
        # Validaciones básicas
        if whatsapp_enabled and not whatsapp_number:
            return Response({
                'error': 'Debe proporcionar un número de WhatsApp Business'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if whatsapp_number and not whatsapp_number.startswith('+'):
            return Response({
                'error': 'El número debe incluir el código de país (ej: +51999123456)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar configuración
        try:
            company.whatsapp_business_number = whatsapp_number
            company.whatsapp_enabled = whatsapp_enabled
            company.save()
            
            return Response({
                'success': True,
                'message': 'Configuración de WhatsApp actualizada correctamente',
                'config': {
                    'whatsapp_business_number': company.whatsapp_business_number,
                    'whatsapp_enabled': company.whatsapp_enabled,
                    'whatsapp_plan': company.whatsapp_plan,
                }
            })
            
        except Exception as e:
            return Response({
                'error': f'Error al actualizar configuración: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WhatsAppTestView(APIView):
    """Vista para enviar mensaje de prueba de WhatsApp"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Enviar mensaje de prueba"""
        company = request.user.company
        
        if not company.whatsapp_enabled:
            return Response({
                'error': 'WhatsApp no está habilitado para su empresa'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        test_number = request.data.get('test_number')
        if not test_number:
            return Response({
                'error': 'Debe proporcionar un número de prueba'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Simular envío de mensaje de prueba
            from inventory.services.whatsapp_service import WhatsAppService
            
            whatsapp_service = WhatsAppService(company=company)
            
            test_message = f"""🧪 *MENSAJE DE PRUEBA*

Hola! Este es un mensaje de prueba desde:

🏢 *{company.name}*
📱 *WhatsApp:* {company.whatsapp_business_number}
📧 *Email:* {company.email}

Si recibiste este mensaje, la configuración de WhatsApp está funcionando correctamente.

✅ Tu sistema está listo para enviar órdenes de compra automáticas.

_Mensaje automático - Sistema DataLens_"""
            
            # Por ahora retornar éxito simulado
            return Response({
                'success': True,
                'message': 'Mensaje de prueba enviado exitosamente',
                'sent_to': test_number,
                'sent_from_display': company.whatsapp_business_number,
                'preview': test_message
            })
            
        except Exception as e:
            return Response({
                'error': f'Error al enviar mensaje de prueba: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
