"""
Vistas para análisis de demanda avanzado y optimización de inventario
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from ..models import (
    DemandPattern, AdvancedDemandForecast, SeasonalPattern,
    InventoryOptimizationModel, StockLevelRecommendation,
    SupplierPerformanceModel, ProcurementOptimization,
    SupplierRiskAnalysis, SupplierROIAnalysis, InventoryTurnoverAnalysis
)
from ..serializers import (
    DemandPatternSerializer, AdvancedDemandForecastSerializer,
    SeasonalPatternSerializer, InventoryOptimizationModelSerializer,
    StockLevelRecommendationSerializer, SupplierPerformanceModelSerializer,
    ProcurementOptimizationSerializer, SupplierRiskAnalysisSerializer,
    SupplierROIAnalysisSerializer, InventoryTurnoverAnalysisSerializer
)
from ..services.demand_analysis_service import DemandAnalysisService
from ..services.inventory_optimization_service import InventoryOptimizationService
from .base_views import ForecastPagination, get_user_company
from inventory.models import Product, Supplier

logger = logging.getLogger(__name__)


class DemandPatternViewSet(viewsets.ModelViewSet):
    """ViewSet para patrones de demanda"""
    serializer_class = DemandPatternSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return DemandPattern.objects.none()
        
        print(f"🔍 DEBUG: Buscando DemandPattern para company {company.name}")
        
        # FIX: Verificar si necesitamos regenerar patrones (si tienen pattern_strength = 0)
        existing_patterns = DemandPattern.objects.filter(product__company=company)
        needs_regeneration = not existing_patterns.exists() or existing_patterns.filter(pattern_strength=0).count() > 0
        
        print(f"🔍 DEBUG: Encontrados {existing_patterns.count()} DemandPattern existentes")
        print(f"🔍 DEBUG: Patrones con strength=0: {existing_patterns.filter(pattern_strength=0).count()}")
        print(f"🔍 DEBUG: Necesita regeneración: {needs_regeneration}")
        
        if needs_regeneration:
            try:
                print("🔍 DEBUG: Regenerando patrones de demanda...")
                
                # Limpiar patrones viejos con strength=0
                existing_patterns.filter(pattern_strength=0).delete()
                
                service = DemandAnalysisService(company)
                patterns = service.analyze_seasonal_patterns()
                print(f"🔍 DEBUG: Generados {len(patterns)} SeasonalityPattern nuevos")
                
                # FIX: Convertir SeasonalityPattern a DemandPattern
                self._convert_seasonality_to_demand_patterns(patterns, company)
                
            except Exception as e:
                print(f"❌ DEBUG: Error regenerating demand patterns: {str(e)}")
                logger.error(f"Error regenerating demand patterns: {str(e)}")
        
        # Obtener todos los patrones (regenerados o existentes)
        queryset = DemandPattern.objects.select_related('product').filter(
            product__company=company
        )
        print(f"🔍 DEBUG: Total final de DemandPattern: {queryset.count()}")
        
        product_id = self.request.query_params.get('product_id')
        pattern_type = self.request.query_params.get('pattern_type')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if pattern_type:
            queryset = queryset.filter(pattern_type=pattern_type)
        if start_date:
            queryset = queryset.filter(pattern_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(pattern_date__lte=end_date)
            
        return queryset.order_by('-pattern_date')
    
    def _convert_seasonality_to_demand_patterns(self, seasonality_patterns, company):
        """Convertir SeasonalityPattern a DemandPattern"""
        print(f"🔍 DEBUG: Convirtiendo {len(seasonality_patterns)} patrones estacionales")
        
        for pattern in seasonality_patterns:
            try:
                # Crear múltiples DemandPattern por cada SeasonalityPattern
                peak_periods = pattern.peak_periods if hasattr(pattern, 'peak_periods') else []
                
                if peak_periods:
                    for peak in peak_periods:
                        DemandPattern.objects.update_or_create(
                            product=pattern.product,
                            pattern_type='seasonal_peak',
                            pattern_date=timezone.now().date(),
                            defaults={
                                'pattern_strength': float(pattern.pattern_strength or 0),
                                'frequency': 'monthly'
                            }
                        )
                        print(f"✅ DEBUG: DemandPattern creado para {pattern.product.name}")
                else:
                    # Crear patrón genérico si no hay picos específicos
                    DemandPattern.objects.update_or_create(
                        product=pattern.product,
                        pattern_type='seasonal',
                        pattern_date=timezone.now().date(),
                        defaults={
                            'pattern_strength': float(pattern.pattern_strength or 0),
                            'frequency': 'monthly'
                        }
                    )
                    print(f"✅ DEBUG: DemandPattern genérico creado para {pattern.product.name}")
                    
            except Exception as e:
                print(f"❌ DEBUG: Error convirtiendo patrón para {pattern.product.name}: {str(e)}")
                continue
    
    @action(detail=False, methods=['post'])
    def analyze_patterns(self, request):
        """Analiza patrones de demanda para productos específicos"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            demand_service = DemandAnalysisService(company)
            patterns = demand_service.analyze_demand_patterns(
                company=company,
                **request.data
            )
            
            serializer = self.get_serializer(patterns, many=True)
            return Response({
                'success': True,
                'patterns': serializer.data,
                'count': len(patterns)
            })
            
        except Exception as e:
            logger.error(f"Error analizando patrones de demanda: {str(e)}")
            return Response({
                'error': 'Error al analizar patrones de demanda',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdvancedDemandForecastViewSet(viewsets.ModelViewSet):
    """ViewSet para pronósticos avanzados de demanda"""
    serializer_class = AdvancedDemandForecastSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return AdvancedDemandForecast.objects.none()
        
        queryset = AdvancedDemandForecast.objects.select_related('product', 'model').filter(
            product__company=company
        )
        
        product_id = self.request.query_params.get('product_id')
        forecast_type = self.request.query_params.get('forecast_type')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if forecast_type:
            queryset = queryset.filter(forecast_type=forecast_type)
        if start_date:
            queryset = queryset.filter(forecast_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(forecast_date__lte=end_date)
            
        return queryset.order_by('-forecast_date')
    
    @action(detail=False, methods=['post'])
    def generate_advanced_forecast(self, request):
        """Genera pronósticos avanzados de demanda"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            demand_service = DemandAnalysisService(company)
            forecasts = demand_service.generate_advanced_demand_forecast(
                company=company,
                **request.data
            )
            
            serializer = self.get_serializer(forecasts, many=True)
            return Response({
                'success': True,
                'forecasts': serializer.data,
                'count': len(forecasts)
            })
            
        except Exception as e:
            logger.error(f"Error generando pronósticos avanzados: {str(e)}")
            return Response({
                'error': 'Error al generar pronósticos avanzados',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SeasonalPatternViewSet(viewsets.ModelViewSet):
    """ViewSet para patrones estacionales"""
    serializer_class = SeasonalPatternSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return SeasonalPattern.objects.none()
        
        queryset = SeasonalPattern.objects.select_related('product').filter(
            product__company=company
        )
        
        product_id = self.request.query_params.get('product_id')
        season_type = self.request.query_params.get('season_type')
        is_active = self.request.query_params.get('is_active')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if season_type:
            queryset = queryset.filter(season_type=season_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-created_at')


class InventoryOptimizationModelViewSet(viewsets.ModelViewSet):
    """ViewSet para modelos de optimización de inventario"""
    serializer_class = InventoryOptimizationModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return InventoryOptimizationModel.objects.none()
        
        queryset = InventoryOptimizationModel.objects.filter(company=company)
        
        model_type = self.request.query_params.get('model_type')
        is_active = self.request.query_params.get('is_active')
        
        if model_type:
            queryset = queryset.filter(model_type=model_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def optimize_inventory(self, request):
        """Optimiza niveles de inventario"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            inventory_service = InventoryOptimizationService(company)
            optimization = inventory_service.optimize_inventory_levels(
                company=company,
                **request.data
            )
            
            return Response({
                'success': True,
                'optimization': optimization,
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error optimizando inventario: {str(e)}")
            return Response({
                'error': 'Error al optimizar inventario',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StockLevelRecommendationViewSet(viewsets.ModelViewSet):
    """ViewSet para recomendaciones de nivel de stock"""
    serializer_class = StockLevelRecommendationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return StockLevelRecommendation.objects.none()
        
        queryset = StockLevelRecommendation.objects.select_related('product', 'model').filter(
            product__company=company
        )
        
        product_id = self.request.query_params.get('product_id')
        recommendation_type = self.request.query_params.get('recommendation_type')
        priority = self.request.query_params.get('priority')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if recommendation_type:
            queryset = queryset.filter(recommendation_type=recommendation_type)
        if priority:
            queryset = queryset.filter(priority=priority)
            
        return queryset.order_by('-created_at')


class SupplierPerformanceModelViewSet(viewsets.ModelViewSet):
    """ViewSet para modelos de rendimiento de proveedores"""
    serializer_class = SupplierPerformanceModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return SupplierPerformanceModel.objects.none()
        
        queryset = SupplierPerformanceModel.objects.select_related('supplier').filter(
            supplier__in=Supplier.objects.filter(
                products__company=company
            ).distinct()
        )
        
        supplier_id = self.request.query_params.get('supplier_id')
        performance_score_min = self.request.query_params.get('performance_score_min')
        
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        if performance_score_min:
            queryset = queryset.filter(
                performance_score__gte=float(performance_score_min)
            )
            
        return queryset.order_by('-analysis_date')


class ProcurementOptimizationViewSet(viewsets.ModelViewSet):
    """ViewSet para optimización de procuramiento"""
    serializer_class = ProcurementOptimizationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return ProcurementOptimization.objects.none()
        
        queryset = ProcurementOptimization.objects.select_related('product', 'supplier').filter(
            product__company=company
        )
        
        product_id = self.request.query_params.get('product_id')
        supplier_id = self.request.query_params.get('supplier_id')
        optimization_type = self.request.query_params.get('optimization_type')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        if optimization_type:
            queryset = queryset.filter(optimization_type=optimization_type)
            
        return queryset.order_by('-analysis_date')


class SupplierRiskAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet para análisis de riesgo de proveedores"""
    serializer_class = SupplierRiskAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return SupplierRiskAnalysis.objects.none()
        
        queryset = SupplierRiskAnalysis.objects.select_related('supplier').filter(
            supplier__in=Supplier.objects.filter(
                products__company=company
            ).distinct()
        )
        
        supplier_id = self.request.query_params.get('supplier_id')
        risk_level = self.request.query_params.get('risk_level')
        risk_type = self.request.query_params.get('risk_type')
        
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        if risk_type:
            queryset = queryset.filter(risk_type=risk_type)
            
        return queryset.order_by('-analysis_date')


class SupplierROIAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet para análisis de ROI de proveedores"""
    serializer_class = SupplierROIAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return SupplierROIAnalysis.objects.none()
        
        queryset = SupplierROIAnalysis.objects.select_related('supplier').filter(
            supplier__in=Supplier.objects.filter(
                products__company=company
            ).distinct()
        )
        
        supplier_id = self.request.query_params.get('supplier_id')
        roi_min = self.request.query_params.get('roi_min')
        
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        if roi_min:
            queryset = queryset.filter(roi_percentage__gte=float(roi_min))
            
        return queryset.order_by('-roi_percentage', '-analysis_start_date')


class InventoryTurnoverAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet para análisis de rotación de inventario"""
    serializer_class = InventoryTurnoverAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return InventoryTurnoverAnalysis.objects.none()
        
        queryset = InventoryTurnoverAnalysis.objects.select_related('product').filter(
            product__company=company
        )
        
        product_id = self.request.query_params.get('product_id')
        turnover_min = self.request.query_params.get('turnover_min')
        period_type = self.request.query_params.get('period_type')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if turnover_min:
            queryset = queryset.filter(turnover_ratio__gte=float(turnover_min))
        if period_type:
            queryset = queryset.filter(period_type=period_type)
            
        return queryset.order_by('-analysis_date')


class DemandAnalysisView(APIView):
    """Vista para análisis integral de demanda"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            demand_service = DemandAnalysisService(company)
            analysis = demand_service.comprehensive_demand_analysis(
                company=company,
                **request.data
            )
            
            return Response({
                'success': True,
                'analysis': analysis,
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error en análisis de demanda: {str(e)}")
            return Response({
                'error': 'Error al realizar análisis de demanda',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InventoryOptimizationView(APIView):
    """Vista para optimización completa de inventario"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener optimización de inventario existente o generar nueva"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = InventoryOptimizationService(company)
            optimization = service.comprehensive_inventory_optimization(company)
            
            return Response({
                'success': True,
                'stock_levels_count': len(optimization.get('stock_levels', [])),
                'stockout_predictions_count': len(optimization.get('stockout_predictions', [])),
                'abc_classifications_count': optimization.get('abc_analysis', {}).get('classification_counts', {}).get('A', 0) + 
                                          optimization.get('abc_analysis', {}).get('classification_counts', {}).get('B', 0) + 
                                          optimization.get('abc_analysis', {}).get('classification_counts', {}).get('C', 0),
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error en optimización de inventario: {str(e)}")
            return Response({
                'error': 'Error al optimizar inventario',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            inventory_service = InventoryOptimizationService(company)
            optimization = inventory_service.comprehensive_inventory_optimization(
                company=company,
                **request.data
            )
            
            return Response({
                'success': True,
                'optimization': optimization,
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error en optimización de inventario: {str(e)}")
            return Response({
                'error': 'Error al optimizar inventario',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


__all__ = [
    'DemandPatternViewSet',
    'AdvancedDemandForecastViewSet',
    'SeasonalPatternViewSet',
    'InventoryOptimizationModelViewSet',
    'StockLevelRecommendationViewSet',
    'SupplierPerformanceModelViewSet',
    'ProcurementOptimizationViewSet',
    'SupplierRiskAnalysisViewSet',
    'SupplierROIAnalysisViewSet',
    'InventoryTurnoverAnalysisViewSet',
    'DemandAnalysisView',
    'InventoryOptimizationView'
]