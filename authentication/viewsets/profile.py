"""
Vistas relacionadas con el perfil y configuraciones del usuario
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema

from ..serializers import ProfileSerializer, ChangePasswordSerializer


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
