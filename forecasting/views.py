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
from datalens_backend.utils import get_default_company

logger = logging.getLogger(__name__)


class ForecastModelViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de modelos de pronóstico"""
    serializer_class = ForecastModelSerializer
    
    def get_queryset(self):
        # Usar empresa con productos peruanos reales
        company = get_default_company()
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
            company = get_default_company()
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
        company = get_default_company()
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
    pagination_class = None  # Desactivar paginación para mostrar todos los productos
    
    def get_queryset(self):
        print(f"🔍 DemandForecastViewSet.get_queryset() - Iniciando...")
        try:
            company = get_default_company()
            print(f"🏢 Empresa obtenida: {company}")
            if not company:
                print("❌ No hay empresa por defecto")
                return DemandForecast.objects.none()
        except Exception as e:
            print(f"❌ Error obteniendo empresa: {e}")
            return DemandForecast.objects.none()
            
        try:
            queryset = DemandForecast.objects.filter(product__company=company)
            count = queryset.count()
            print(f"📊 Total de pronósticos en BD para empresa {company.name}: {count}")
            
            # Debug: Ver todos los pronósticos en la BD
            all_forecasts = DemandForecast.objects.all()
            print(f"📈 Total de pronósticos en toda la BD: {all_forecasts.count()}")
            
            if all_forecasts.exists():
                sample = all_forecasts.first()
                print(f"🎯 Ejemplo de pronóstico: {sample.id} - {sample.product.name if sample.product else 'Sin producto'}")
            
            # Filtros opcionales
            product_id = self.request.query_params.get('product_id')
            model_id = self.request.query_params.get('model_id')
            days_ahead = self.request.query_params.get('days_ahead')
            
            print(f"🔧 Filtros aplicados - product_id: {product_id}, model_id: {model_id}, days_ahead: {days_ahead}")
            
            if product_id:
                queryset = queryset.filter(product_id=product_id)
                print(f"📦 Filtrado por producto {product_id}: {queryset.count()} resultados")
            if model_id:
                queryset = queryset.filter(model_id=model_id)
                print(f"🤖 Filtrado por modelo {model_id}: {queryset.count()} resultados")
            if days_ahead:
                future_date = datetime.now().date() + timedelta(days=int(days_ahead))
                queryset = queryset.filter(forecast_date__lte=future_date)
                print(f"📅 Filtrado por fecha hasta {future_date}: {queryset.count()} resultados")
                
            final_queryset = queryset.order_by('product__name', 'forecast_date')
            final_count = final_queryset.count()
            print(f"✅ Queryset final: {final_count} pronósticos")
            
            return final_queryset
        except Exception as e:
            print(f"❌ Error en query de pronósticos: {e}")
            return DemandForecast.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            # En caso de error, devolver respuesta vacía pero válida
            return Response({
                'count': 0,
                'results': [],
                'message': 'No forecasting data available',
                'error': f'Forecasting service temporarily unavailable: {str(e)}'
            })


class ReorderRecommendationViewSet(viewsets.ModelViewSet):
    """ViewSet para recomendaciones de reorden"""
    serializer_class = ReorderRecommendationSerializer
    
    def get_queryset(self):
        print(f"🔍 ReorderRecommendationViewSet.get_queryset() - Iniciando...")
        try:
            company = get_default_company()
            print(f"🏢 Empresa obtenida para recomendaciones: {company}")
            if not company:
                print("❌ No hay empresa por defecto para recomendaciones")
                return ReorderRecommendation.objects.none()
        except Exception as e:
            print(f"❌ Error obteniendo empresa para recomendaciones: {e}")
            return ReorderRecommendation.objects.none()
            
        try:
            queryset = ReorderRecommendation.objects.filter(product__company=company)
            count = queryset.count()
            print(f"📊 Total de recomendaciones en BD para empresa {company.name}: {count}")
            
            # Debug: Ver todas las recomendaciones en la BD
            all_recommendations = ReorderRecommendation.objects.all()
            print(f"📈 Total de recomendaciones en toda la BD: {all_recommendations.count()}")
            
            if all_recommendations.exists():
                sample = all_recommendations.first()
                print(f"🎯 Ejemplo de recomendación: {sample.id} - {sample.product.name if sample.product else 'Sin producto'}")
            
            # Filtros opcionales
            priority = self.request.query_params.get('priority')
            product_id = self.request.query_params.get('product_id')
            status_filter = self.request.query_params.get('status')
            
            print(f"🔧 Filtros aplicados - priority: {priority}, product_id: {product_id}, status: {status_filter}")
            
            if priority:
                queryset = queryset.filter(priority=priority)
                print(f"⚡ Filtrado por prioridad {priority}: {queryset.count()} resultados")
            if product_id:
                queryset = queryset.filter(product_id=product_id)
                print(f"📦 Filtrado por producto {product_id}: {queryset.count()} resultados")
            if status_filter:
                queryset = queryset.filter(status=status_filter)
                print(f"📋 Filtrado por status {status_filter}: {queryset.count()} resultados")
                
            final_queryset = queryset.order_by('-created_at')
            final_count = final_queryset.count()
            print(f"✅ Queryset final de recomendaciones: {final_count} items")
            
            return final_queryset
        except Exception as e:
            print(f"❌ Error en query de recomendaciones: {e}")
            return ReorderRecommendation.objects.none()
    

class PredictDemandView(APIView):
    """Vista para generar pronósticos de demanda"""
    
    def post(self, request):
        print(f"🚀 PredictDemandView.post() - Iniciando generación de pronósticos...")
        print(f"📝 Datos recibidos: {request.data}")
        
        serializer = PredictDemandRequestSerializer(data=request.data)
        if serializer.is_valid():
            print(f"✅ Serializer válido")
            company = get_default_company()
            print(f"🏢 Empresa para pronósticos: {company}")
            if not company:
                print("❌ No se encontró empresa")
                return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
                
            product_ids = serializer.validated_data.get('product_ids')
            forecast_horizon = serializer.validated_data.get('forecast_horizon', 30)
            include_confidence = serializer.validated_data.get('include_confidence_intervals', True)
            
            print(f"🔧 Parámetros: product_ids={product_ids}, horizon={forecast_horizon}, confidence={include_confidence}")
            
            try:
                forecast_service = ForecastService()
                print(f"🤖 ForecastService creado")
                
                if product_ids:
                    products = Product.objects.filter(id__in=product_ids, company=company)
                    print(f"📦 Productos específicos encontrados: {products.count()}")
                else:
                    products = Product.objects.filter(company=company, is_active=True)
                    print(f"📦 Productos activos de la empresa: {products.count()}")
                
                if not products.exists():
                    print("❌ No se encontraron productos para procesar")
                    return Response({
                        'error': 'No se encontraron productos para generar pronósticos',
                        'details': 'Verifique que existen productos activos en la empresa'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                results = []
                for i, product in enumerate(products):
                    print(f"📈 Procesando producto {i+1}/{products.count()}: {product.name} (ID: {product.id})")
                    try:
                        forecasts = forecast_service.generate_forecasts(
                            product, forecast_horizon, include_confidence
                        )
                        print(f"✅ Pronósticos generados para {product.name}: {len(forecasts)} items")
                        results.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'forecasts_count': len(forecasts),
                            'status': 'success'
                        })
                    except Exception as e:
                        print(f"❌ Error generando pronóstico para {product.sku}: {str(e)}")
                        logger.error(f"Error generando pronóstico para {product.sku}: {str(e)}")
                        results.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'status': 'error',
                            'error': str(e)
                        })
                
                print(f"🎯 Resultado final: {len(results)} productos procesados")
                response_data = {
                    'message': f'Pronósticos generados para {len(results)} productos',
                    'results': results,
                    'forecast_horizon_days': forecast_horizon
                }
                print(f"📤 Respuesta enviada: {response_data}")
                return Response(response_data)
                
            except Exception as e:
                print(f"❌ Error general en predicción: {str(e)}")
                logger.error(f"Error general en predicción: {str(e)}")
                return Response({
                    'error': 'Error al generar pronósticos',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print(f"❌ Serializer inválido: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainModelView(APIView):
    """Vista para entrenar modelos individuales"""
    
    def post(self, request):
        serializer = TrainModelRequestSerializer(data=request.data)
        if serializer.is_valid():
            company = get_default_company()
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
        company = get_default_company()
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
        company = get_default_company()
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
        company = get_default_company()
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
    
    @action(detail=False, methods=['post'])
    def generate_forecasts_ml(self, request):
        """
        Genera pronósticos usando el sistema ML robusto
        """
        try:
            company = get_default_company()
            if not company:
                return Response({
                    'success': False,
                    'message': 'No se encontró empresa por defecto'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"🚀 Iniciando generación de pronósticos ML para {company.name}")
            
            # Obtener productos de la empresa
            products = Product.objects.filter(company=company, is_active=True)
            
            if not products.exists():
                return Response({
                    'success': False,
                    'message': 'No hay productos activos para generar pronósticos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"📦 Procesando {products.count()} productos")
            
            # Inicializar servicio de forecasting
            forecast_service = ForecastService()
            
            total_forecasts = 0
            processed_products = 0
            errors = []
            
            # Generar pronósticos para cada producto
            for product in products:
                try:
                    print(f"🔄 Procesando {product.name}...")
                    
                    # Generar pronósticos ML para este producto
                    forecasts = forecast_service.generate_forecasts(
                        product=product,
                        forecast_horizon=30,
                        include_confidence=True
                    )
                    
                    total_forecasts += len(forecasts)
                    processed_products += 1
                    
                    print(f"✅ {len(forecasts)} pronósticos creados para {product.name}")
                    
                except Exception as e:
                    error_msg = f"Error procesando {product.name}: {str(e)}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                    continue
            
            # Respuesta de resultados
            success_rate = (processed_products / products.count()) * 100
            
            response_data = {
                'success': True,
                'message': f'Pronósticos ML generados exitosamente',
                'results': {
                    'total_products': products.count(),
                    'processed_products': processed_products,
                    'total_forecasts_created': total_forecasts,
                    'success_rate': f"{success_rate:.1f}%",
                    'company': company.name
                }
            }
            
            if errors:
                response_data['warnings'] = errors
            
            print(f"🎯 Proceso completado: {processed_products}/{products.count()} productos, {total_forecasts} pronósticos")
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            error_msg = f"Error en generación de pronósticos ML: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MLModelViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de modelos de ML"""
    serializer_class = ForecastModelSerializer
    
    def get_queryset(self):
        # Usar empresa con productos peruanos reales
        company = get_default_company()
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
            company = get_default_company()
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
        company = get_default_company()
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
    
    @action(detail=True, methods=['post'])
    def test_model(self, request, pk=None):
        """Endpoint para probar un modelo específico"""
        try:
            ml_model = self.get_object()
            service = MLModelService()
            
            # Probar entrenamiento
            train_success = service.retrain_model(ml_model.id)
            
            if not train_success:
                return Response(
                    {'error': 'Error entrenando modelo'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Refrescar desde DB
            ml_model.refresh_from_db()
            
            # Probar predicción
            try:
                predictions = service.generate_forecast(ml_model.id, days_ahead=5)
                prediction_success = len(predictions) > 0 if predictions else False
            except Exception as e:
                prediction_success = False
                prediction_error = str(e)
            
            return Response({
                'model_id': ml_model.id,
                'training_success': True,
                'mae': float(ml_model.mae) if ml_model.mae else None,
                'mape': float(ml_model.mape) if ml_model.mape else None,
                'status': ml_model.status,
                'prediction_success': prediction_success,
                'prediction_error': prediction_error if not prediction_success else None,
                'last_trained': ml_model.last_trained
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
