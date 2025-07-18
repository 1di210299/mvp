"""
Vistas para análisis financiero y pronósticos avanzados
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import logging

from ..models import (
    FinancialForecastModel, RevenuePrediction, CashFlowForecast,
    ProfitabilityAnalysis, FinancialRiskAssessment, SeasonalityAnalysis,
    CostOptimizationModel, RevenueBreakdown, FinancialScenario,
    ProfitMarginAnalysis, FinancialTrendAnalysis
)
from ..serializers import (
    FinancialForecastModelSerializer, RevenuePredictionSerializer,
    CashFlowForecastSerializer, ProfitabilityAnalysisSerializer,
    FinancialRiskAssessmentSerializer, SeasonalityAnalysisSerializer,
    CostOptimizationModelSerializer, RevenueBreakdownSerializer,
    FinancialScenarioSerializer, ProfitMarginAnalysisSerializer,
    FinancialTrendAnalysisSerializer
)
from ..services.financial_forecasting_service import FinancialForecastingService
from .base_views import ForecastPagination, get_user_company

logger = logging.getLogger(__name__)


class FinancialForecastModelViewSet(viewsets.ModelViewSet):
    """ViewSet para modelos de pronóstico financiero"""
    serializer_class = FinancialForecastModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return FinancialForecastModel.objects.none()
        
        queryset = FinancialForecastModel.objects.filter(company=company)
        
        # Filtros opcionales
        model_type = self.request.query_params.get('model_type')
        is_active = self.request.query_params.get('is_active')
        
        if model_type:
            queryset = queryset.filter(model_type=model_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def train_financial_model(self, request):
        """Entrena un nuevo modelo financiero"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            financial_service = FinancialForecastingService()
            model = financial_service.train_financial_forecast_model(
                company=company,
                **request.data
            )
            
            serializer = self.get_serializer(model)
            return Response({
                'success': True,
                'model': serializer.data,
                'message': 'Modelo financiero entrenado exitosamente'
            })
            
        except Exception as e:
            logger.error(f"Error entrenando modelo financiero: {str(e)}")
            return Response({
                'error': 'Error al entrenar modelo financiero',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RevenuePredictionViewSet(viewsets.ModelViewSet):
    """ViewSet para predicciones de ingresos"""
    serializer_class = RevenuePredictionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return RevenuePrediction.objects.none()
        
        queryset = RevenuePrediction.objects.select_related('model').filter(
            model__company=company
        )
        
        # Si no hay datos de revenue, generar automáticamente
        if not queryset.exists():
            try:
                from forecasting.services.financial_forecasting_service import FinancialForecastingService
                service = FinancialForecastingService(company)
                
                # Crear un modelo financiero básico primero
                financial_model = service.create_revenue_forecast_model(
                    metric_type='revenue',
                    horizon_days=90
                )
                
                # Generar predicciones de ingresos
                revenue_predictions = service.generate_revenue_predictions(
                    financial_model=financial_model,
                    period_type='monthly',
                    periods_ahead=6
                )
                logger.info(f"Generated {len(revenue_predictions)} revenue predictions for company {company.name}")
                
                # Refrescar queryset después de generar datos
                queryset = RevenuePrediction.objects.select_related('model').filter(
                    model__company=company
                )
            except Exception as e:
                logger.error(f"Error auto-generating revenue data: {str(e)}")
        
        # Filtros opcionales
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(prediction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(prediction_date__lte=end_date)
            
        return queryset.order_by('-prediction_date')
    
    @action(detail=False, methods=['post'])
    def generate_predictions(self, request):
        """Genera nuevas predicciones de ingresos"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            financial_service = FinancialForecastingService(company)
            
            # Crear un modelo financiero básico primero
            financial_model = financial_service.create_revenue_forecast_model(
                metric_type='revenue',
                horizon_days=90
            )
            
            # Generar predicciones de ingresos
            predictions = financial_service.generate_revenue_predictions(
                financial_model=financial_model,
                period_type='monthly',
                periods_ahead=6
            )
            
            serializer = self.get_serializer(predictions, many=True)
            return Response({
                'success': True,
                'predictions': serializer.data,
                'count': len(predictions)
            })
            
        except Exception as e:
            logger.error(f"Error generando predicciones de ingresos: {str(e)}")
            return Response({
                'error': 'Error al generar predicciones de ingresos',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CashFlowForecastViewSet(viewsets.ModelViewSet):
    """ViewSet para pronósticos de flujo de caja"""
    serializer_class = CashFlowForecastSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return CashFlowForecast.objects.none()
        
        queryset = CashFlowForecast.objects.select_related('model').filter(
            model__company=company
        )
        
        # Filtros opcionales
        forecast_type = self.request.query_params.get('forecast_type')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if forecast_type:
            queryset = queryset.filter(forecast_type=forecast_type)
        if start_date:
            queryset = queryset.filter(period_start__gte=start_date)
        if end_date:
            queryset = queryset.filter(period_end__lte=end_date)
            
        return queryset.order_by('-period_start')


class ProfitabilityAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet para análisis de rentabilidad"""
    serializer_class = ProfitabilityAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return ProfitabilityAnalysis.objects.none()
        
        queryset = ProfitabilityAnalysis.objects.select_related('product').filter(
            product__company=company
        )
        
        # Filtros opcionales
        product_id = self.request.query_params.get('product_id')
        analysis_type = self.request.query_params.get('analysis_type')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if analysis_type:
            queryset = queryset.filter(analysis_type=analysis_type)
            
        return queryset.order_by('-analysis_date')


class FinancialRiskAssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet para evaluación de riesgos financieros"""
    serializer_class = FinancialRiskAssessmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return FinancialRiskAssessment.objects.none()
        
        queryset = FinancialRiskAssessment.objects.filter(company=company)
        
        # Filtros opcionales
        risk_type = self.request.query_params.get('risk_type')
        risk_level = self.request.query_params.get('risk_level')
        
        if risk_type:
            queryset = queryset.filter(risk_type=risk_type)
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
            
        return queryset.order_by('-assessment_date')


class SeasonalityAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet para análisis de estacionalidad"""
    serializer_class = SeasonalityAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return SeasonalityAnalysis.objects.none()
        
        queryset = SeasonalityAnalysis.objects.select_related('product').filter(
            product__company=company
        )
        
        # Filtros opcionales
        product_id = self.request.query_params.get('product_id')
        season_type = self.request.query_params.get('season_type')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if season_type:
            queryset = queryset.filter(season_type=season_type)
            
        return queryset.order_by('-analysis_date')


class CostOptimizationModelViewSet(viewsets.ModelViewSet):
    """ViewSet para modelos de optimización de costos"""
    serializer_class = CostOptimizationModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return CostOptimizationModel.objects.none()
        
        return CostOptimizationModel.objects.filter(company=company).order_by('-created_at')


class RevenueBreakdownViewSet(viewsets.ModelViewSet):
    """ViewSet para desglose de ingresos"""
    serializer_class = RevenueBreakdownSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return RevenueBreakdown.objects.none()
        
        queryset = RevenueBreakdown.objects.select_related('product').filter(
            product__company=company
        )
        
        # Filtros opcionales
        product_id = self.request.query_params.get('product_id')
        breakdown_type = self.request.query_params.get('breakdown_type')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if breakdown_type:
            queryset = queryset.filter(breakdown_type=breakdown_type)
            
        return queryset.order_by('-period_start')


class FinancialScenarioViewSet(viewsets.ModelViewSet):
    """ViewSet para escenarios financieros"""
    serializer_class = FinancialScenarioSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return FinancialScenario.objects.none()
        
        queryset = FinancialScenario.objects.filter(company=company)
        
        # Filtros opcionales
        scenario_type = self.request.query_params.get('scenario_type')
        is_active = self.request.query_params.get('is_active')
        
        if scenario_type:
            queryset = queryset.filter(scenario_type=scenario_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-created_at')


class ProfitMarginAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet para análisis de margen de beneficio"""
    serializer_class = ProfitMarginAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return ProfitMarginAnalysis.objects.none()
        
        queryset = ProfitMarginAnalysis.objects.select_related('product').filter(
            product__company=company
        )
        
        # Filtros opcionales
        product_id = self.request.query_params.get('product_id')
        margin_type = self.request.query_params.get('margin_type')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if margin_type:
            queryset = queryset.filter(margin_type=margin_type)
            
        return queryset.order_by('-analysis_date')


class FinancialTrendAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet para análisis de tendencias financieras"""
    serializer_class = FinancialTrendAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return FinancialTrendAnalysis.objects.none()
        
        return FinancialTrendAnalysis.objects.filter(company=company).order_by('-analysis_date')


class FinancialDashboardView(APIView):
    """Vista para dashboard financiero con métricas clave"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            financial_service = FinancialForecastingService()
            dashboard_data = financial_service.get_financial_dashboard(company)
            
            return Response({
                'success': True,
                'dashboard': dashboard_data,
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error generando dashboard financiero: {str(e)}")
            return Response({
                'error': 'Error al generar dashboard financiero',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinancialReportView(APIView):
    """Vista para generar reportes financieros personalizados"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            financial_service = FinancialForecastingService()
            report_data = financial_service.generate_financial_report(
                company=company,
                **request.data
            )
            
            return Response({
                'success': True,
                'report': report_data,
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error generando reporte financiero: {str(e)}")
            return Response({
                'error': 'Error al generar reporte financiero',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


__all__ = [
    'FinancialForecastModelViewSet',
    'RevenuePredictionViewSet',
    'CashFlowForecastViewSet', 
    'ProfitabilityAnalysisViewSet',
    'FinancialRiskAssessmentViewSet',
    'SeasonalityAnalysisViewSet',
    'CostOptimizationModelViewSet',
    'RevenueBreakdownViewSet',
    'FinancialScenarioViewSet',
    'ProfitMarginAnalysisViewSet',
    'FinancialTrendAnalysisViewSet',
    'FinancialDashboardView',
    'FinancialReportView'
]
