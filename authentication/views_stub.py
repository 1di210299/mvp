from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Company, User


class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet temporal para Company - implementar completamente después"""
    queryset = Company.objects.none()
    
    def list(self, request):
        return Response([])


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet temporal para User - implementar completamente después"""
    queryset = User.objects.none()
    
    def list(self, request):
        return Response([])


class RegisterView(APIView):
    """Vista temporal para registro"""
    
    def post(self, request):
        return Response({
            'status': 'success',
            'message': 'Funcionalidad en desarrollo'
        })


class ProfileView(APIView):
    """Vista temporal para perfil"""
    
    def get(self, request):
        return Response({
            'status': 'success',
            'message': 'Funcionalidad en desarrollo'
        })


class ChangePasswordView(APIView):
    """Vista temporal para cambio de contraseña"""
    
    def post(self, request):
        return Response({
            'status': 'success',
            'message': 'Funcionalidad en desarrollo'
        })
