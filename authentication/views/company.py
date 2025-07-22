"""
Vistas relacionadas con gestión de empresas y configuraciones
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from ..models import Company, User
from ..serializers import CompanySerializer, UserSerializer, UserCreateSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de empresas"""
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    queryset = Company.objects.all()
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'superadmin':
            return Company.objects.all()
        return Company.objects.filter(id=user.company.id)
    
    @extend_schema(
        summary="Obtener estadísticas de la empresa",
        description="Retorna estadísticas básicas de la empresa como usuarios activos, productos, etc."
    )
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        company = self.get_object()
        stats = {
            'total_users': company.users.filter(is_active=True).count(),
            'total_products': company.products.filter(is_active=True).count() if hasattr(company, 'products') else 0,
            'total_locations': company.locations.filter(is_active=True).count() if hasattr(company, 'locations') else 0,
            'total_suppliers': company.suppliers.filter(is_active=True).count() if hasattr(company, 'suppliers') else 0,
            'subscription_type': company.subscription_type,
            'max_users': company.max_users,
        }
        return Response(stats)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'superadmin':
            return User.objects.all()
        elif user.role == 'admin':
            return User.objects.filter(company=user.company)
        else:
            return User.objects.filter(id=user.id)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def perform_create(self, serializer):
        # Solo admin y superadmin pueden crear usuarios
        user = self.request.user
        if user.role not in ['admin', 'superadmin']:
            raise permissions.PermissionDenied("No tienes permisos para crear usuarios")
        
        # Si no es superadmin, asignar a su empresa
        if user.role != 'superadmin':
            serializer.save(company=user.company)
        else:
            serializer.save()
    
    @extend_schema(
        summary="Activar/desactivar usuario",
        description="Cambia el estado activo del usuario"
    )
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response({
            'status': 'success',
            'is_active': user.is_active
        })


class CompanyWhatsAppConfigView(APIView):
    """Vista para configurar WhatsApp de la empresa"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener configuración actual de WhatsApp"""
        company = request.user.company
        
        config = {
            'company_name': company.name,
            'whatsapp_business_number': getattr(company, 'whatsapp_business_number', ''),
            'whatsapp_enabled': getattr(company, 'whatsapp_enabled', False),
            'whatsapp_plan': getattr(company, 'whatsapp_plan', 'basic'),
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
        if hasattr(company, 'whatsapp_business_number'):
            company.whatsapp_business_number = whatsapp_number
        if hasattr(company, 'whatsapp_enabled'):
            company.whatsapp_enabled = whatsapp_enabled
        
        company.save()
        
        return Response({
            'message': 'Configuración de WhatsApp actualizada exitosamente',
            'config': {
                'whatsapp_business_number': whatsapp_number,
                'whatsapp_enabled': whatsapp_enabled
            }
        })


class WhatsAppTestView(APIView):
    """Vista para probar conexión de WhatsApp"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Probar envío de mensaje de WhatsApp"""
        company = request.user.company
        test_number = request.data.get('test_number', '').strip()
        
        if not test_number:
            return Response({
                'error': 'Debe proporcionar un número de prueba'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not getattr(company, 'whatsapp_enabled', False):
            return Response({
                'error': 'WhatsApp no está habilitado para esta empresa'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simular envío de mensaje de prueba
        # En producción aquí iría la lógica real de WhatsApp API
        return Response({
            'message': 'Mensaje de prueba enviado exitosamente',
            'test_number': test_number,
            'status': 'sent'
        })
