"""
Views para onboarding y configuración de tenants
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import redirect
from django.http import HttpResponse

from inventory.services.tenant_onboarding_service import TenantOnboardingService
from authentication.models import Company

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def setup_new_tenant(request):
    """
    POST /api/tenant/setup
    Configuración completa de un nuevo tenant
    """
    try:
        company_id = request.data.get('company_id')
        admin_email = request.data.get('admin_email')
        
        if not company_id or not admin_email:
            return Response(
                {'error': 'company_id y admin_email son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {'error': 'Empresa no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Ejecutar setup completo
        onboarding_service = TenantOnboardingService()
        result = onboarding_service.complete_tenant_setup(company, admin_email)
        
        if result['success']:
            return Response({
                'success': True,
                'message': f'Tenant {company.name} configurado exitosamente',
                'setup_results': result['results'],
                'next_steps': result['next_steps']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': result.get('error')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    except Exception as e:
        logger.error(f"Error en setup de tenant: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gmail_oauth_start(request):
    """
    GET /api/tenant/gmail-oauth/start
    Iniciar flujo OAuth2 de Gmail
    """
    try:
        company = request.user.company
        redirect_uri = request.build_absolute_uri('/api/tenant/gmail-oauth/callback/')
        
        onboarding_service = TenantOnboardingService()
        result = onboarding_service.generate_gmail_oauth_url(company.id, redirect_uri)
        
        if result['success']:
            return redirect(result['auth_url'])
        else:
            return Response(
                {'error': result.get('error')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    except Exception as e:
        logger.error(f"Error iniciando Gmail OAuth: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def gmail_oauth_callback(request):
    """
    GET /api/tenant/gmail-oauth/callback/
    Callback de OAuth2 de Gmail
    """
    try:
        code = request.GET.get('code')
        state = request.GET.get('state')
        
        if not code or not state:
            return HttpResponse(
                "<h1>Error: Autorización cancelada o parámetros faltantes</h1>",
                status=400
            )
        
        redirect_uri = request.build_absolute_uri('/api/tenant/gmail-oauth/callback/')
        
        onboarding_service = TenantOnboardingService()
        result = onboarding_service.handle_gmail_oauth_callback(code, state, redirect_uri)
        
        if result['success']:
            return HttpResponse(f"""
                <h1>✅ Gmail OAuth Configurado Exitosamente</h1>
                <p>La empresa {result['company_id']} ya puede enviar y recibir emails automáticamente.</p>
                <p>Puedes cerrar esta ventana y regresar a DataLens.</p>
                <script>
                    setTimeout(function() {{
                        window.close();
                    }}, 3000);
                </script>
            """)
        else:
            return HttpResponse(f"""
                <h1>❌ Error en Gmail OAuth</h1>
                <p>Error: {result.get('error')}</p>
                <p>Por favor contacta al administrador del sistema.</p>
            """, status=500)
    
    except Exception as e:
        logger.error(f"Error en Gmail OAuth callback: {str(e)}")
        return HttpResponse(f"""
            <h1>❌ Error Interno</h1>
            <p>Error: {str(e)}</p>
        """, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tenant_status(request):
    """
    GET /api/tenant/status
    Verificar estado de configuración del tenant
    """
    try:
        company = request.user.company
        
        onboarding_service = TenantOnboardingService()
        result = onboarding_service.validate_tenant_configuration(company)
        
        if result['success']:
            return Response({
                'success': True,
                'company_name': company.name,
                'validation': result['validation'],
                'is_ready': result['validation']['is_fully_configured']
            })
        else:
            return Response(
                {'error': result.get('error')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    except Exception as e:
        logger.error(f"Error verificando status del tenant: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_integrations(request):
    """
    POST /api/tenant/test
    Probar integraciones configuradas
    """
    try:
        company = request.user.company
        test_type = request.data.get('test_type', 'all')  # 'whatsapp', 'gmail', 'all'
        
        results = {
            'company': company.name,
            'tests': {}
        }
        
        # Aquí implementarías pruebas específicas
        if test_type in ['whatsapp', 'all']:
            # Probar envío de WhatsApp
            results['tests']['whatsapp'] = {
                'success': True,
                'message': 'WhatsApp test pendiente de implementación'
            }
        
        if test_type in ['gmail', 'all']:
            # Probar envío de Gmail
            results['tests']['gmail'] = {
                'success': True,
                'message': 'Gmail test pendiente de implementación'
            }
        
        return Response({
            'success': True,
            'test_results': results
        })
    
    except Exception as e:
        logger.error(f"Error probando integraciones: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
