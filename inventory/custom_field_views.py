"""
Views para manejo de campos personalizados y análisis con IA
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
import json

from .models import Product, Supplier, Category, CustomFieldDefinition, CustomFieldValue
from .ai_analytics import OpenAIAnalyticsService
from .serializers import ProductSerializer, SupplierSerializer, CategorySerializer


class CustomFieldDefinitionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar definiciones de campos personalizados"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CustomFieldDefinition.objects.filter(
            company=self.request.user.company,
            is_active=True
        )
    
    def create(self, request):
        """Crear nueva definición de campo personalizado"""
        data = request.data.copy()
        data['company'] = request.user.company.id
        
        try:
            field_def = CustomFieldDefinition.objects.create(
                company=request.user.company,
                model_type=data['model_type'],
                field_name=data['field_name'],
                field_label=data['field_label'],
                field_type=data['field_type'],
                is_required=data.get('is_required', False),
                default_value=data.get('default_value', ''),
                help_text=data.get('help_text', ''),
                choices_json=data.get('choices_json', ''),
                min_value=data.get('min_value'),
                max_value=data.get('max_value'),
                min_length=data.get('min_length'),
                max_length=data.get('max_length'),
                order=data.get('order', 0)
            )
            
            return Response({
                'id': field_def.id,
                'field_name': field_def.field_name,
                'field_label': field_def.field_label,
                'field_type': field_def.field_type,
                'model_type': field_def.model_type,
                'message': 'Campo personalizado creado exitosamente'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Error creando campo personalizado: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_model(self, request):
        """Obtener campos personalizados por tipo de modelo"""
        model_type = request.query_params.get('model_type')
        if not model_type:
            return Response({'error': 'model_type es requerido'}, status=400)
        
        fields = self.get_queryset().filter(model_type=model_type)
        
        result = []
        for field in fields:
            result.append({
                'id': field.id,
                'field_name': field.field_name,
                'field_label': field.field_label,
                'field_type': field.field_type,
                'is_required': field.is_required,
                'default_value': field.default_value,
                'help_text': field.help_text,
                'choices': field.get_choices(),
                'order': field.order
            })
        
        return Response(result)


class ProductViewSetExtended(viewsets.ModelViewSet):
    """ViewSet extendido para productos con campos personalizados"""
    
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.company)
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener producto con campos personalizados"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Agregar campos personalizados
        data = serializer.data
        data['custom_fields'] = instance.get_custom_field_values()
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def set_custom_field(self, request, pk=None):
        """Establecer valor de campo personalizado"""
        product = self.get_object()
        field_name = request.data.get('field_name')
        value = request.data.get('value')
        
        if not field_name:
            return Response({'error': 'field_name es requerido'}, status=400)
        
        try:
            product.set_custom_field_value(field_name, value)
            return Response({
                'message': f'Campo {field_name} actualizado exitosamente'
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['get'])
    def ai_insights(self, request, pk=None):
        """Obtener insights de IA para el producto"""
        product = self.get_object()
        
        try:
            service = OpenAIAnalyticsService()
            insights = service.generate_demand_forecast(product.id)
            return Response(insights)
        except Exception as e:
            return Response({
                'error': f'Error obteniendo insights: {str(e)}'
            }, status=500)


class AIAnalyticsViewSet(viewsets.GenericViewSet):
    """ViewSet para análisis con IA"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def inventory_analysis(self, request):
        """Análisis completo de inventario con IA"""
        try:
            service = OpenAIAnalyticsService()
            analysis = service.analyze_inventory_trends(
                request.user.company.id,
                custom_fields_data=None
            )
            return Response(analysis)
        except Exception as e:
            return Response({
                'error': f'Error en análisis: {str(e)}'
            }, status=500)
    
    @action(detail=False, methods=['post'])
    def custom_fields_insights(self, request):
        """Análisis de insights para campos personalizados"""
        model_type = request.data.get('model_type', 'product')
        
        try:
            service = OpenAIAnalyticsService()
            insights = service.analyze_custom_fields_insights(
                request.user.company.id,
                model_type
            )
            return Response(insights)
        except Exception as e:
            return Response({
                'error': f'Error en análisis: {str(e)}'
            }, status=500)
    
    @action(detail=False, methods=['post'])
    def suggest_fields(self, request):
        """Sugerir campos personalizados basado en IA"""
        model_type = request.data.get('model_type', 'product')
        business_context = request.data.get('business_context', '')
        
        try:
            service = OpenAIAnalyticsService()
            suggestions = service.suggest_custom_fields(
                request.user.company.id,
                model_type,
                business_context
            )
            return Response(suggestions)
        except Exception as e:
            return Response({
                'error': f'Error generando sugerencias: {str(e)}'
            }, status=500)
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generar reporte inteligente"""
        report_type = request.data.get('report_type', 'inventory_summary')
        custom_filters = request.data.get('filters', {})
        
        try:
            service = OpenAIAnalyticsService()
            report = service.generate_intelligent_report(
                request.user.company.id,
                report_type,
                custom_filters
            )
            return Response(report)
        except Exception as e:
            return Response({
                'error': f'Error generando reporte: {str(e)}'
            }, status=500)
    
    @action(detail=False, methods=['get'])
    def dashboard_insights(self, request):
        """Obtener insights para dashboard principal"""
        try:
            service = OpenAIAnalyticsService()
            
            # Análisis básico de inventario
            inventory_analysis = service.analyze_inventory_trends(
                request.user.company.id
            )
            
            # Insights de campos personalizados
            custom_insights = service.analyze_custom_fields_insights(
                request.user.company.id,
                'product'
            )
            
            # Combinar insights
            dashboard_data = {
                'inventory_insights': inventory_analysis,
                'custom_fields_insights': custom_insights,
                'recommendations': [],
                'alerts': []
            }
            
            return Response(dashboard_data)
            
        except Exception as e:
            return Response({
                'error': f'Error obteniendo insights: {str(e)}'
            }, status=500)


# Funciones auxiliares

def get_model_with_custom_fields(model_class, pk, company):
    """Obtiene un modelo con sus campos personalizados"""
    instance = get_object_or_404(model_class, pk=pk, company=company)
    
    # Serializar datos base
    if model_class == Product:
        serializer = ProductSerializer(instance)
    elif model_class == Supplier:
        serializer = SupplierSerializer(instance)
    elif model_class == Category:
        serializer = CategorySerializer(instance)
    else:
        return None
    
    data = serializer.data
    data['custom_fields'] = instance.get_custom_field_values()
    
    return data

def bulk_update_custom_fields(model_class, company_id, updates):
    """Actualización masiva de campos personalizados"""
    results = []
    
    for update in updates:
        try:
            instance = model_class.objects.get(
                id=update['id'],
                company_id=company_id
            )
            
            for field_name, value in update.get('custom_fields', {}).items():
                instance.set_custom_field_value(field_name, value)
            
            results.append({
                'id': instance.id,
                'status': 'success',
                'message': 'Campos actualizados'
            })
            
        except Exception as e:
            results.append({
                'id': update.get('id'),
                'status': 'error',
                'message': str(e)
            })
    
    return results
