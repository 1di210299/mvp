from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import datetime, timedelta
import logging

from .models import ForecastModel, DemandForecast, ReorderRecommendation
from .serializers import (
    ForecastModelSerializer, DemandForecastSerializer, ReorderRecommendationSerializer,
    TrainModelRequestSerializer, PredictDemandRequestSerializer, ModelComparisonSerializer,
    ForecastChartDataSerializer, ProductForecastSummarySerializer
)
from .services.ml_model_service import MLModelService
from .services.forecast_service import ForecastService
from .services.evaluation_service import EvaluationService
from .tasks import (
    train_ml_model, generate_forecasts_for_model, 
    evaluate_ml_model, compare_model_algorithms
)
from inventory.models import Product
from authentication.models import Company

logger = logging.getLogger(__name__)


class ForecastModelViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de modelos de pronóstico"""
    serializer_class = ForecastModelSerializer
    
    def get_queryset(self):
        # Usar la primera empresa disponible (temporal - sin autenticación)
        company = Company.objects.first()
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
        """Entrena modelos de ML"""
        serializer = TrainModelRequestSerializer(data=request.data)
        if serializer.is_valid():
            company = Company.objects.first()
            if not company:
                return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
                
            product_ids = serializer.validated_data.get('product_ids')
            algorithm = serializer.validated_data.get('algorithm', 'prophet')
            retrain_existing = serializer.validated_data.get('retrain_existing', False)
            async_training = serializer.validated_data.get('async_training', False)
            
            try:
                ml_service = MLModelService()
                results = ml_service.train_models_for_company(
                    company, product_ids, algorithm, retrain_existing
                )
                return Response({
                    'message': 'Modelos entrenados exitosamente',
                    'results': results
                })
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
        company = Company.objects.first()
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
    """ViewSet para pronósticos de demanda"""
    serializer_class = DemandForecastSerializer
    
    def get_queryset(self):
        company = Company.objects.first()
        if not company:
            return DemandForecast.objects.none()
            
        queryset = DemandForecast.objects.filter(product__company=company)
        
        # Filtros opcionales
        product_id = self.request.query_params.get('product_id')
        model_id = self.request.query_params.get('model_id')
        days_ahead = self.request.query_params.get('days_ahead')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if model_id:
            queryset = queryset.filter(model_id=model_id)
        if days_ahead:
            future_date = datetime.now().date() + timedelta(days=int(days_ahead))
            queryset = queryset.filter(forecast_date__lte=future_date)
            
        return queryset.order_by('-created_at', 'forecast_date')


class ReorderRecommendationViewSet(viewsets.ModelViewSet):
    """ViewSet para recomendaciones de reorden"""
    serializer_class = ReorderRecommendationSerializer
    
    def get_queryset(self):
        company = Company.objects.first()
        if not company:
            return ReorderRecommendation.objects.none()
            
        queryset = ReorderRecommendation.objects.filter(product__company=company)
        
        # Filtros opcionales
        priority = self.request.query_params.get('priority')
        product_id = self.request.query_params.get('product_id')
        status_filter = self.request.query_params.get('status')
        
        if priority:
            queryset = queryset.filter(priority=priority)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-created_at')


class PredictDemandView(APIView):
    """Vista para generar pronósticos de demanda"""
    
    def post(self, request):
        serializer = PredictDemandRequestSerializer(data=request.data)
        if serializer.is_valid():
            company = Company.objects.first()
            if not company:
                return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
                
            product_ids = serializer.validated_data.get('product_ids')
            forecast_horizon = serializer.validated_data.get('forecast_horizon', 30)
            include_confidence = serializer.validated_data.get('include_confidence_intervals', True)
            
            try:
                forecast_service = ForecastService()
                
                if product_ids:
                    products = Product.objects.filter(id__in=product_ids, company=company)
                else:
                    products = Product.objects.filter(company=company, is_active=True)
                
                results = []
                for product in products:
                    try:
                        forecasts = forecast_service.generate_forecasts(
                            product, forecast_horizon, include_confidence
                        )
                        results.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'forecasts_count': len(forecasts),
                            'status': 'success'
                        })
                    except Exception as e:
                        logger.error(f"Error generando pronóstico para {product.sku}: {str(e)}")
                        results.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'status': 'error',
                            'error': str(e)
                        })
                
                return Response({
                    'message': f'Pronósticos generados para {len(results)} productos',
                    'results': results,
                    'forecast_horizon_days': forecast_horizon
                })
                
            except Exception as e:
                logger.error(f"Error general en predicción: {str(e)}")
                return Response({
                    'error': 'Error al generar pronósticos',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainModelView(APIView):
    """Vista para entrenar modelos individuales"""
    
    def post(self, request):
        serializer = TrainModelRequestSerializer(data=request.data)
        if serializer.is_valid():
            company = Company.objects.first()
            if not company:
                return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
                
            product_ids = serializer.validated_data.get('product_ids', [])
            algorithm = serializer.validated_data.get('algorithm', 'prophet')
            retrain_existing = serializer.validated_data.get('retrain_existing', False)
            
            try:
                ml_service = MLModelService()
                
                if product_ids:
                    products = Product.objects.filter(id__in=product_ids, company=company)
                else:
                    products = Product.objects.filter(company=company, is_active=True)
                
                trained_models = []
                for product in products:
                    try:
                        model = ml_service.train_model_for_product(
                            product, algorithm, retrain_existing
                        )
                        if model:
                            trained_models.append({
                                'product_id': product.id,
                                'product_name': product.name,
                                'model_id': model.id,
                                'model_type': model.model_type,
                                'status': 'trained'
                            })
                    except Exception as e:
                        logger.error(f"Error entrenando modelo para {product.sku}: {str(e)}")
                        trained_models.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'status': 'error',
                            'error': str(e)
                        })
                
                return Response({
                    'message': f'Entrenamiento completado para {len(trained_models)} productos',
                    'models': trained_models
                })
                
            except Exception as e:
                logger.error(f"Error en entrenamiento: {str(e)}")
                return Response({
                    'error': 'Error durante el entrenamiento',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModelAccuracyView(APIView):
    """Vista para obtener métricas de precisión de un modelo"""
    
    def get(self, request, model_id):
        company = Company.objects.first()
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            model = get_object_or_404(
                ForecastModel, 
                id=model_id, 
                company=company
            )
            
            evaluation_service = EvaluationService()
            accuracy_report = evaluation_service.evaluate_model_accuracy(model)
            
            return Response({
                'model_id': model.id,
                'model_name': model.name,
                'model_type': model.model_type,
                'product': {
                    'id': model.product.id,
                    'name': model.product.name,
                    'sku': model.product.sku
                },
                'accuracy_metrics': {
                    'mae': model.mae,
                    'mape': model.mape,
                    'rmse': model.rmse,
                    'r2_score': model.r2_score
                },
                'detailed_report': accuracy_report,
                'last_trained': model.training_completed_at,
                'last_evaluated': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo precisión del modelo {model_id}: {str(e)}")
            return Response({
                'error': 'Error al evaluar modelo',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductForecastView(APIView):
    """Vista para obtener pronósticos completos de un producto"""
    
    def get(self, request, product_id):
        company = Company.objects.first()
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = get_object_or_404(Product, id=product_id, company=company)
            
            # Obtener pronósticos recientes
            forecasts = DemandForecast.objects.filter(
                product=product
            ).order_by('-created_at', 'forecast_date')[:30]
            
            # Obtener recomendaciones de reorden
            recommendations = ReorderRecommendation.objects.filter(
                product=product
            ).order_by('-created_at')[:5]
            
            # Obtener el mejor modelo
            best_model = ForecastModel.objects.filter(
                product=product,
                status='active'
            ).order_by('-training_completed_at').first()
            
            # Datos para gráficos (últimos 90 días + próximos 30 días)
            forecast_service = ForecastService()
            chart_data = forecast_service.get_forecast_chart_data(product, days_back=90, days_ahead=30)
            
            summary_data = {
                'product_id': product.id,
                'product_name': product.name,
                'product_sku': product.sku,
                'forecasts': DemandForecastSerializer(forecasts, many=True).data,
                'recommendations': ReorderRecommendationSerializer(recommendations, many=True).data,
                'best_model': ForecastModelSerializer(best_model).data if best_model else None,
                'chart_data': chart_data
            }
            
            return Response(summary_data)
            
        except Exception as e:
            logger.error(f"Error obteniendo pronósticos del producto {product_id}: {str(e)}")
            return Response({
                'error': 'Error al obtener pronósticos del producto',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateRecommendationsView(APIView):
    """Vista para generar recomendaciones de reorden"""
    
    def post(self, request):
        company = Company.objects.first()
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
            
        product_ids = request.data.get('product_ids', [])
        
        try:
            forecast_service = ForecastService()
            
            if product_ids:
                products = Product.objects.filter(id__in=product_ids, company=company)
            else:
                products = Product.objects.filter(company=company, is_active=True)
            
            # Generar recomendaciones para la empresa completa
            recommendations = forecast_service.generate_reorder_recommendations(
                company_id=company.id,
                products=list(products) if product_ids else None
            )
            
            recommendations_created = []
            for rec in recommendations:
                recommendations_created.append({
                    'product_id': rec.product.id,
                    'product_name': rec.product.name,
                    'recommendation_id': rec.id,
                    'priority': rec.priority,
                    'quantity': float(rec.recommended_quantity),
                    'current_stock': float(rec.current_stock),
                    'expected_stockout_date': rec.expected_stockout_date.isoformat() if rec.expected_stockout_date else None
                })
            
            return Response({
                'message': f'Recomendaciones generadas: {len(recommendations_created)}',
                'recommendations': recommendations_created
            })
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return Response({
                'error': 'Error al generar recomendaciones',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
