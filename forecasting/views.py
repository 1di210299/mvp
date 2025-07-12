from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
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
from .services import ChartService
from .tasks import (
    train_ml_model, generate_forecasts_for_model, 
    evaluate_ml_model, compare_model_algorithms
)
from inventory.models import Product
from authentication.models import Company
from datalens_backend.utils import get_default_company

logger = logging.getLogger(__name__)


class ForecastPagination(PageNumberPagination):
    """Paginación optimizada para pronósticos"""
    page_size = 50  # Solo 50 pronósticos por página
    page_size_query_param = 'page_size'
    max_page_size = 100  # Máximo 100 items por página

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
    """ViewSet para pronósticos de demanda con paginación optimizada"""
    serializer_class = DemandForecastSerializer
    pagination_class = ForecastPagination  # Activar paginación
    
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
            # Optimizar query con select_related para evitar N+1 queries
            queryset = DemandForecast.objects.select_related(
                'product', 'model'
            ).filter(product__company=company)
            
            count = queryset.count()
            print(f"📊 Total de pronósticos en BD para empresa {company.name}: {count}")
            
            # Filtros opcionales para reducir datos
            product_id = self.request.query_params.get('product_id')
            model_id = self.request.query_params.get('model_id')
            days_ahead = self.request.query_params.get('days_ahead')
            recent_only = self.request.query_params.get('recent_only', 'true')  # Por defecto solo recientes
            
            print(f"🔧 Filtros aplicados - product_id: {product_id}, model_id: {model_id}, days_ahead: {days_ahead}, recent_only: {recent_only}")
            
            # Filtro por fechas recientes (últimos 7 días + próximos 30 días)
            if recent_only.lower() == 'true':
                recent_date = datetime.now().date() - timedelta(days=7)
                future_date = datetime.now().date() + timedelta(days=30)
                queryset = queryset.filter(
                    forecast_date__gte=recent_date,
                    forecast_date__lte=future_date
                )
                print(f"📅 Filtrado por fechas recientes ({recent_date} a {future_date}): {queryset.count()} resultados")
            
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
                
            # Ordenar por fecha de pronóstico más reciente primero
            final_queryset = queryset.order_by('-created_at', 'forecast_date')
            final_count = final_queryset.count()
            print(f"✅ Queryset final: {final_count} pronósticos (con paginación)")
            
            return final_queryset
        except Exception as e:
            print(f"❌ Error en query de pronósticos: {e}")
            return DemandForecast.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list con manejo robusto de errores y límites"""
        try:
            # Verificar si se solicitan demasiados datos sin filtros
            queryset = self.filter_queryset(self.get_queryset())
            
            # Si hay más de 1000 items sin filtros específicos, forzar filtros
            if queryset.count() > 1000:
                product_id = request.query_params.get('product_id')
                recent_only = request.query_params.get('recent_only', 'true')
                
                if not product_id and recent_only.lower() != 'true':
                    return Response({
                        'error': 'Demasiados datos solicitados',
                        'message': 'Use filtros como product_id o recent_only=true para limitar los resultados',
                        'total_available': queryset.count(),
                        'suggestion': 'Agregue ?recent_only=true&page_size=50 a su solicitud'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Paginación estándar
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            # Fallback sin paginación (solo para querysets pequeños)
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
            
        except Exception as e:
            print(f"❌ Error en list de pronósticos: {e}")
            # En caso de error, devolver respuesta vacía pero válida
            return Response({
                'count': 0,
                'results': [],
                'message': 'No forecasting data available',
                'error': f'Forecasting service temporarily unavailable: {str(e)}'
            })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Endpoint optimizado para obtener resumen de pronósticos"""
        try:
            company = get_default_company()
            if not company:
                return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Solo obtener estadísticas básicas sin datos completos
            total_forecasts = DemandForecast.objects.filter(product__company=company).count()
            recent_forecasts = DemandForecast.objects.filter(
                product__company=company,
                created_at__gte=datetime.now() - timedelta(days=7)
            ).count()
            
            # Contar productos con pronósticos
            products_with_forecasts = DemandForecast.objects.filter(
                product__company=company
            ).values('product').distinct().count()
            
            return Response({
                'total_forecasts': total_forecasts,
                'recent_forecasts': recent_forecasts,
                'products_with_forecasts': products_with_forecasts,
                'company': company.name,
                'last_updated': datetime.now()
            })
            
        except Exception as e:
            print(f"❌ Error en summary: {e}")
            return Response({
                'error': 'Error getting forecast summary',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class DemandForecastChartView(APIView):
    """
    Vista para generar gráficos de proyecciones de demanda
    """
    # permission_classes = [IsAuthenticated]  # Comentado para pruebas
    
    def get(self, request):
        """
        GET /api/forecasting/charts/demand/
        Genera gráfico de proyecciones de demanda
        
        Parámetros:
        - chart_type: line, bar, area (default: line)
        - days_ahead: días a proyectar (default: 7)
        - product_ids: IDs de productos separados por coma
        - location_ids: IDs de ubicaciones separados por coma
        """
        try:
            # Obtener empresa por defecto
            company = get_default_company()
            if not company:
                return Response({
                    'error': 'No se encontró empresa por defecto'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener parámetros
            chart_type = request.query_params.get('chart_type', 'line')
            days_ahead = int(request.query_params.get('days_ahead', 7))
            
            # Procesar product_ids
            product_ids = request.query_params.get('product_ids')
            if product_ids:
                product_ids = [int(id.strip()) for id in product_ids.split(',') if id.strip()]
            
            # Procesar location_ids
            location_ids = request.query_params.get('location_ids')
            if location_ids:
                location_ids = [int(id.strip()) for id in location_ids.split(',') if id.strip()]
            
            # Generar gráfico
            chart_service = ChartService()
            result = chart_service.generate_demand_forecast_chart(
                company_id=company.id,  # Usar empresa por defecto
                product_ids=product_ids,
                location_ids=location_ids,
                days_ahead=days_ahead,
                chart_type=chart_type
            )
            
            if 'error' in result:
                return Response({
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'chart_image': result['chart_image'],
                'data': result['data'],
                'stats': result['stats'],
                'total_points': result['total_points']
            })
            
        except ValueError as e:
            return Response({
                'error': f'Parámetros inválidos: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error generando gráfico de demanda: {str(e)}")
            return Response({
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ModelComparisonChartView(APIView):
    """
    Vista para generar gráficos de comparación de modelos ML
    """
    # permission_classes = [IsAuthenticated]  # Comentado para pruebas
    
    def get(self, request):
        """
        GET /api/forecasting/charts/models/
        Genera gráfico de comparación entre modelos ML
        """
        try:
            # Obtener empresa por defecto
            company = get_default_company()
            if not company:
                return Response({
                    'error': 'No se encontró empresa por defecto'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            chart_service = ChartService()
            result = chart_service.generate_model_comparison_chart(
                company_id=company.id  # Usar empresa por defecto
            )
            
            if 'error' in result:
                return Response({
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'chart_image': result['chart_image'],
                'models_data': result['models_data']
            })
            
        except Exception as e:
            logger.error(f"Error generando gráfico de comparación: {str(e)}")
            return Response({
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ForecastDataView(APIView):
    """
    Vista para obtener datos de pronósticos en formato JSON
    """
    # permission_classes = [IsAuthenticated]  # Comentado para pruebas
    
    def get(self, request):
        """
        GET /api/forecasting/data/
        Obtiene datos de pronósticos para gráficos del frontend
        """
        try:
            # Obtener empresa por defecto
            company = get_default_company()
            if not company:
                return Response({
                    'error': 'No se encontró empresa por defecto'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener parámetros
            days_ahead = int(request.query_params.get('days_ahead', 7))
            product_ids = request.query_params.get('product_ids')
            location_ids = request.query_params.get('location_ids')
            
            # Procesar IDs
            if product_ids:
                product_ids = [int(id.strip()) for id in product_ids.split(',') if id.strip()]
            if location_ids:
                location_ids = [int(id.strip()) for id in location_ids.split(',') if id.strip()]
            
            # Obtener datos usando el servicio de gráficos
            chart_service = ChartService()
            data = chart_service._get_forecast_data(
                company_id=company.id,  # Usar empresa por defecto
                product_ids=product_ids,
                location_ids=location_ids,
                days_ahead=days_ahead
            )
            
            if data.empty:
                return Response({
                    'error': 'No hay datos de pronósticos disponibles',
                    'data': []
                })
            
            # Preparar datos para el frontend
            chart_data = chart_service._prepare_chart_data(data)
            stats = chart_service._calculate_stats(data)
            
            return Response({
                'success': True,
                'data': chart_data,
                'stats': stats,
                'total_points': len(data)
            })
            
        except ValueError as e:
            return Response({
                'error': f'Parámetros inválidos: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error obteniendo datos de pronósticos: {str(e)}")
            return Response({
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
