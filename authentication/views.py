from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Company, User
from .serializers import (
    CompanySerializer, UserSerializer, UserCreateSerializer,
    RegisterSerializer, ProfileSerializer, ChangePasswordSerializer
)


class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de empresas"""
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    
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


class RegisterView(APIView):
    """Vista para registro de nuevos usuarios y empresas"""
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    @extend_schema(
        summary="Registrar nueva empresa y usuario administrador",
        description="Crea una nueva empresa junto con el primer usuario administrador"
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                
                # Generar tokens JWT
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'status': 'success',
                    'message': 'Registro exitoso',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """Vista para gestión del perfil del usuario"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener perfil del usuario",
        description="Retorna la información del perfil del usuario autenticado"
    )
    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Actualizar perfil del usuario",
        description="Actualiza la información del perfil del usuario autenticado"
    )
    def patch(self, request):
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Perfil actualizado exitosamente',
                'data': serializer.data
            })
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Vista para cambio de contraseña"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Cambiar contraseña del usuario",
        description="Permite al usuario cambiar su contraseña actual"
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'status': 'success',
                'message': 'Contraseña cambiada exitosamente'
            })
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
