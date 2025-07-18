"""
Vistas principales para forecasting y gestión de modelos ML
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import datetime, timedelta
import logging

from ..models import ForecastModel, DemandForecast, ReorderRecommendation
from ..serializers import (
    ForecastModelSerializer, DemandForecastSerializer, ReorderRecommendationSerializer,
    TrainModelRequestSerializer, PredictDemandRequestSerializer, ModelComparisonSerializer,
    ForecastChartDataSerializer, ProductForecastSummarySerializer
)
# Importar servicios ML
from ..services import ForecastService
from ..ml_algorithms.training_service import training_service
from ..services.ml_model_service import MLModelService
from ..services.forecast_service import ForecastService
from ..services.evaluation_service import EvaluationService
from ..services import ChartService
from ..tasks import (
    train_ml_model, generate_forecasts_for_model, 
    evaluate_ml_model, compare_model_algorithms
)
from inventory.models import Product
from authentication.models import Company
from .base_views import ForecastPagination, get_user_company

logger = logging.getLogger(__name__)


class ForecastModelViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de modelos de pronóstico"""
    serializer_class = ForecastModelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return ForecastModel.objects.none()
            
        queryset = ForecastModel.objects.filter(company=company)
        
        # Filtros opcionales
        model_type = self.request.query_params.get('model_type')
        status_filter = self.request.query_params.get('status')
        product_id = self.request.query_params.get('product_id')
        
        if model_type:
            queryset = queryset.filter(model_type=model_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
            
        return queryset.order_by('-training_completed_at', '-created_at')
    
    @action(detail=False, methods=['post'])
    def train_models(self, request):
        """Entrena modelos de ML usando el nuevo servicio"""
        serializer = TrainModelRequestSerializer(data=request.data)
        if serializer.is_valid():
            company = get_user_company(request)
            if not company:
                return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
                
            model_id = serializer.validated_data.get('model_id')
            model_type = serializer.validated_data.get('model_type', 'prophet')
            
            try:
                # Buscar el modelo por ID o crear uno nuevo
                if model_id:
                    forecast_model = ForecastModel.objects.get(id=model_id, company=company)
                else:
                    # Crear modelo temporal para entrenamiento
                    forecast_model = ForecastModel.objects.create(
                        company=company,
                        name=f'Test {model_type.title()} Model',
                        model_type=model_type,
                        status='training'
                    )
                
                # Entrenar usando el nuevo servicio
                result = training_service.train_model(forecast_model)
                
                if result['success']:
                    return Response({
                        'message': 'Modelo entrenado exitosamente',
                        'model_id': forecast_model.id,
                        'status': forecast_model.status
                    })
                else:
                    return Response({
                        'error': 'Error durante el entrenamiento',
                        'details': result.get('error', 'Error desconocido')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except ForecastModel.DoesNotExist:
                return Response({
                    'error': 'Modelo no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error en entrenamiento: {str(e)}")
                return Response({
                    'error': 'Error durante el entrenamiento de modelos',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def comparison(self, request):
        """Compara modelos de diferentes algoritmos"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
            
        product_id = request.query_params.get('product_id')
        
        try:
            evaluation_service = EvaluationService()
            if product_id:
                # Comparación para un producto específico
                product = get_object_or_404(Product, id=product_id, company=company)
                comparison = evaluation_service.compare_models_for_product(product)
            else:
                # Comparación general
                comparison = evaluation_service.compare_all_models(company)
            
            serializer = ModelComparisonSerializer(comparison, many=True)
            return Response({
                'comparison': serializer.data,
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error en comparación de modelos: {str(e)}")
            return Response({
                'error': 'Error al comparar modelos',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DemandForecastViewSet(viewsets.ModelViewSet):
    """ViewSet para pronósticos de demanda con paginación optimizada"""
    serializer_class = DemandForecastSerializer
    pagination_class = ForecastPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        logger.info("🔍 DemandForecastViewSet.get_queryset() - Iniciando...")
        try:
            company = get_user_company(self.request)
            logger.info(f"🏢 Empresa obtenida: {company}")
            if not company:
                logger.warning("❌ No hay empresa por defecto")
                return DemandForecast.objects.none()
        except Exception as e:
            logger.error(f"❌ Error obteniendo empresa: {e}")
            return DemandForecast.objects.none()
            
        try:
            # Optimizar query con select_related para evitar N+1 queries
            queryset = DemandForecast.objects.select_related(
                'product', 'model'
            ).filter(product__company=company)
            
            count = queryset.count()
            logger.info(f"📊 Total de pronósticos en BD para empresa {company.name}: {count}")
            
            # Filtros opcionales para reducir datos
            product_id = self.request.query_params.get('product_id')
            model_id = self.request.query_params.get('model_id')
            days_ahead = self.request.query_params.get('days_ahead')
            recent_only = self.request.query_params.get('recent_only', 'true')
            
            logger.info(f"🔧 Filtros aplicados - product_id: {product_id}, model_id: {model_id}, days_ahead: {days_ahead}, recent_only: {recent_only}")
            
            # Filtro por fechas recientes (últimos 7 días + próximos 30 días)
            if recent_only.lower() == 'true':
                recent_date = datetime.now().date() - timedelta(days=7)
                future_date = datetime.now().date() + timedelta(days=30)
                queryset = queryset.filter(
                    forecast_date__gte=recent_date,
                    forecast_date__lte=future_date
                )
                logger.info(f"📅 Filtrado por fechas recientes ({recent_date} a {future_date}): {queryset.count()} resultados")
            
            if product_id:
                queryset = queryset.filter(product_id=product_id)
                logger.info(f"📦 Filtrado por producto {product_id}: {queryset.count()} resultados")
            if model_id:
                queryset = queryset.filter(model_id=model_id)
                logger.info(f"🤖 Filtrado por modelo {model_id}: {queryset.count()} resultados")
            if days_ahead:
                future_date = datetime.now().date() + timedelta(days=int(days_ahead))
                queryset = queryset.filter(forecast_date__lte=future_date)
                logger.info(f"📅 Filtrado por fecha hasta {future_date}: {queryset.count()} resultados")
                
            # Ordenar por fecha de pronóstico más reciente primero
            final_queryset = queryset.order_by('-created_at', 'forecast_date')
            final_count = final_queryset.count()
            logger.info(f"✅ Queryset final: {final_count} pronósticos (con paginación)")
            
            return final_queryset
        except Exception as e:
            logger.error(f"❌ Error en query de pronósticos: {e}")
            return DemandForecast.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list con manejo robusto de errores y límites"""
        try:
            # Verificar si se solicitan demasiados datos sin filtros
            queryset = self.filter_queryset(self.get_queryset())
            
            # Si hay más de 1000 resultados sin filtros específicos, limitar automáticamente
            if queryset.count() > 1000 and not any([
                request.query_params.get('product_id'),
                request.query_params.get('model_id'),
                request.query_params.get('days_ahead')
            ]):
                logger.warning("⚠️ Demasiados resultados sin filtros - limitando automáticamente")
                # Aplicar filtro automático de fechas recientes
                recent_date = datetime.now().date() - timedelta(days=7)
                future_date = datetime.now().date() + timedelta(days=30)
                queryset = queryset.filter(
                    forecast_date__gte=recent_date,
                    forecast_date__lte=future_date
                )
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.info(f"📄 Devolviendo página con {len(page)} pronósticos")
                result = self.get_paginated_response(serializer.data)
                
                # Agregar metadatos útiles
                result.data['meta'] = {
                    'total_forecasts': queryset.count(),
                    'filters_applied': {
                        'product_id': request.query_params.get('product_id'),
                        'model_id': request.query_params.get('model_id'),
                        'days_ahead': request.query_params.get('days_ahead'),
                        'recent_only': request.query_params.get('recent_only', 'true')
                    }
                }
                return result

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"❌ Error en list de DemandForecast: {e}")
            return Response({
                'error': 'Error al obtener pronósticos',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReorderRecommendationViewSet(viewsets.ModelViewSet):
    """ViewSet para recomendaciones de reorden"""
    serializer_class = ReorderRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return ReorderRecommendation.objects.none()
            
        queryset = ReorderRecommendation.objects.select_related(
            'product'
        ).filter(product__company=company)
        
        # Filtros opcionales
        product_id = self.request.query_params.get('product_id')
        priority = self.request.query_params.get('priority')
        status_filter = self.request.query_params.get('status')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if priority:
            queryset = queryset.filter(priority=priority)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-urgency_score', '-created_at')


class PredictDemandView(APIView):
    """Vista para predicción de demanda usando ML real"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PredictDemandRequestSerializer(data=request.data)
        if serializer.is_valid():
            company = get_user_company(request)
            if not company:
                return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                model_id = serializer.validated_data.get('model_id')
                periods = serializer.validated_data.get('periods') or serializer.validated_data.get('forecast_horizon', 30)
                
                if model_id:
                    # Usar modelo específico
                    try:
                        forecast_model = ForecastModel.objects.get(id=model_id, company=company)
                        forecast_service = ForecastService()
                        result = forecast_service.generate_forecasts_for_model(
                            model_id=model_id,
                            periods=periods
                        )
                    except ForecastModel.DoesNotExist:
                        return Response({
                            'error': 'Modelo no encontrado'
                        }, status=status.HTTP_404_NOT_FOUND)
                else:
                    # Usar el primer modelo activo disponible o el más reciente
                    forecast_model = ForecastModel.objects.filter(
                        company=company,
                        status='active'
                    ).order_by('-created_at').first()
                    
                    if not forecast_model:
                        # Si no hay modelos activos, buscar el modelo más reciente
                        forecast_model = ForecastModel.objects.filter(
                            company=company
                        ).order_by('-created_at').first()
                        
                        if forecast_model:
                            # Marcar como activo si no está fallido
                            if forecast_model.status != 'failed':
                                forecast_model.status = 'active'
                                forecast_model.save()
                        else:
                            return Response({
                                'error': 'No hay modelos disponibles'
                            }, status=status.HTTP_400_BAD_REQUEST)
                    
                    forecast_service = ForecastService()
                    result = forecast_service.generate_forecasts_for_model(
                        model_id=forecast_model.id,
                        periods=periods
                    )
                
                if result.get('success', True):
                    return Response({
                        'success': True,
                        'forecast': result.get('forecast', []),
                        'model_type': result.get('model_type'),
                        'generated_at': datetime.now()
                    })
                else:
                    return Response({
                        'error': 'Error generando predicciones',
                        'details': result.get('error')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Error en predicción: {str(e)}")
                return Response({
                    'error': 'Error al generar predicciones',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainModelView(APIView):
    """Vista para entrenamiento de modelos"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TrainModelRequestSerializer(data=request.data)
        if serializer.is_valid():
            company = get_user_company(request)
            if not company:
                return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                ml_service = MLModelService()
                result = ml_service.train_model(
                    company=company,
                    **serializer.validated_data
                )
                
                return Response({
                    'success': True,
                    'model_id': result.get('model_id'),
                    'message': 'Modelo entrenado exitosamente'
                })
                
            except Exception as e:
                logger.error(f"Error en entrenamiento: {str(e)}")
                return Response({
                    'error': 'Error al entrenar modelo',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModelComparisonView(APIView):
    """Vista para comparación de modelos"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            evaluation_service = EvaluationService()
            comparison = evaluation_service.compare_all_models(company)
            
            serializer = ModelComparisonSerializer(comparison, many=True)
            return Response({
                'comparison': serializer.data,
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error en comparación: {str(e)}")
            return Response({
                'error': 'Error al comparar modelos',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForecastChartView(APIView):
    """Vista para datos de gráficos de pronósticos"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = request.query_params.get('product_id')
        days_ahead = int(request.query_params.get('days_ahead', 30))
        
        try:
            chart_service = ChartService()
            chart_data = chart_service.get_forecast_chart_data(
                company=company,
                product_id=product_id,
                days_ahead=days_ahead
            )
            
            serializer = ForecastChartDataSerializer(chart_data)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error en gráficos: {str(e)}")
            return Response({
                'error': 'Error al generar datos de gráfico',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductForecastSummaryView(APIView):
    """Vista para resumen de pronósticos por producto"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            forecast_service = ForecastService()
            summary = forecast_service.get_product_forecast_summary(company)
            
            serializer = ProductForecastSummarySerializer(summary, many=True)
            return Response({
                'summary': serializer.data,
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error en resumen: {str(e)}")
            return Response({
                'error': 'Error al generar resumen',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


__all__ = [
    'ForecastModelViewSet',
    'DemandForecastViewSet', 
    'ReorderRecommendationViewSet',
    'PredictDemandView',
    'TrainModelView',
    'ModelComparisonView',
    'ForecastChartView',
    'ProductForecastSummaryView'
]
