"""
ViewSets para manejo de modelos Company y User
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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
            'total_products': company.products.filter(is_active=True).count(),
            'total_locations': company.locations.filter(is_active=True).count(),
            'total_suppliers': company.suppliers.filter(is_active=True).count(),
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
