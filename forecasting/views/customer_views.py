"""
Vistas para Customer Intelligence - CRM + ML avanzado
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import logging

# Importar modelos necesarios
from inventory.models import Customer, Sale

from ..models import (
    CustomerLifetimeValue, ChurnPrediction, CustomerSegmentation,
    MarketBasketAnalysis, CustomerBehaviorPattern, PriceOptimization,
    CrossSellModel, CustomerSatisfactionModel, LoyaltyProgramModel,
    CustomerEngagementModel
)
from ..serializers import (
    CustomerLifetimeValueSerializer, ChurnPredictionSerializer,
    CustomerSegmentationSerializer, MarketBasketAnalysisSerializer,
    CustomerBehaviorPatternSerializer, PriceOptimizationSerializer,
    CrossSellModelSerializer, CustomerSatisfactionModelSerializer,
    LoyaltyProgramModelSerializer, CustomerEngagementModelSerializer
)
from ..services.advanced_ml_service import CustomerIntelligenceService
from .base_views import ForecastPagination, get_user_company
from inventory.models import Product, Customer

logger = logging.getLogger(__name__)


class CustomerLifetimeValueViewSet(viewsets.ModelViewSet):
    """ViewSet para Customer Lifetime Value"""
    serializer_class = CustomerLifetimeValueSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return CustomerLifetimeValue.objects.none()
        
        # Filtrar por clientes sin campo company (Customer no tiene este campo)
        # En su lugar, filtramos por ventas de productos de la empresa
        company_customers = Customer.objects.filter(
            name__in=Sale.objects.filter(
                product__company=company
            ).values_list('customer_name', flat=True).distinct()
        )
        
        queryset = CustomerLifetimeValue.objects.select_related('customer').filter(
            customer__in=company_customers
        )
        
        # Filtros opcionales
        customer_id = self.request.query_params.get('customer_id')
        clv_min = self.request.query_params.get('clv_min')
        prediction_horizon = self.request.query_params.get('prediction_horizon')
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if clv_min:
            queryset = queryset.filter(predicted_clv__gte=float(clv_min))
        if prediction_horizon:
            queryset = queryset.filter(prediction_horizon=prediction_horizon)
            
        return queryset.order_by('-predicted_clv', '-calculation_date')
    
    @action(detail=False, methods=['post'])
    def calculate_clv(self, request):
        """Calcula CLV para clientes específicos"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer_service = CustomerIntelligenceService()
            clv_results = customer_service.calculate_customer_lifetime_value(
                company=company,
                **request.data
            )
            
            serializer = self.get_serializer(clv_results, many=True)
            return Response({
                'success': True,
                'clv_results': serializer.data,
                'count': len(clv_results)
            })
            
        except Exception as e:
            logger.error(f"Error calculando CLV: {str(e)}")
            return Response({
                'error': 'Error al calcular Customer Lifetime Value',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChurnPredictionViewSet(viewsets.ModelViewSet):
    """ViewSet para predicción de churn"""
    serializer_class = ChurnPredictionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return ChurnPrediction.objects.none()
        
        # Filtrar por clientes de la empresa
        queryset = ChurnPrediction.objects.select_related('customer').filter(
            customer__in=Customer.objects.filter(company=company)
        )
        
        # Filtros opcionales
        customer_id = self.request.query_params.get('customer_id')
        churn_risk = self.request.query_params.get('churn_risk')
        probability_min = self.request.query_params.get('probability_min')
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if churn_risk:
            queryset = queryset.filter(churn_risk=churn_risk)
        if probability_min:
            queryset = queryset.filter(churn_probability__gte=float(probability_min))
            
        return queryset.order_by('-churn_probability', '-prediction_date')
    
    @action(detail=False, methods=['post'])
    def predict_churn(self, request):
        """Predice churn para clientes"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer_service = CustomerIntelligenceService()
            churn_predictions = customer_service.predict_customer_churn(
                company=company,
                **request.data
            )
            
            serializer = self.get_serializer(churn_predictions, many=True)
            return Response({
                'success': True,
                'churn_predictions': serializer.data,
                'count': len(churn_predictions)
            })
            
        except Exception as e:
            logger.error(f"Error prediciendo churn: {str(e)}")
            return Response({
                'error': 'Error al predecir churn de clientes',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerSegmentationViewSet(viewsets.ModelViewSet):
    """ViewSet para segmentación de clientes"""
    serializer_class = CustomerSegmentationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return CustomerSegmentation.objects.none()
        
        # Filtrar por clientes de la empresa
        queryset = CustomerSegmentation.objects.select_related('customer').filter(
            customer__in=Customer.objects.filter(company=company)
        )
        
        # Filtros opcionales
        customer_id = self.request.query_params.get('customer_id')
        segment_name = self.request.query_params.get('segment_name')
        segmentation_type = self.request.query_params.get('segmentation_type')
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if segment_name:
            queryset = queryset.filter(segment_name__icontains=segment_name)
        if segmentation_type:
            queryset = queryset.filter(segmentation_type=segmentation_type)
            
        return queryset.order_by('-segmentation_date')
    
    @action(detail=False, methods=['post'])
    def create_segmentation(self, request):
        """Crea nueva segmentación de clientes"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer_service = CustomerIntelligenceService()
            segmentation = customer_service.segment_customers(
                company=company,
                **request.data
            )
            
            serializer = self.get_serializer(segmentation, many=True)
            return Response({
                'success': True,
                'segmentation': serializer.data,
                'count': len(segmentation)
            })
            
        except Exception as e:
            logger.error(f"Error en segmentación: {str(e)}")
            return Response({
                'error': 'Error al segmentar clientes',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketBasketAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet para análisis de market basket"""
    serializer_class = MarketBasketAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return MarketBasketAnalysis.objects.none()
        
        # Filtrar por productos de la empresa
        queryset = MarketBasketAnalysis.objects.select_related(
            'primary_product', 'associated_product'
        ).filter(
            primary_product__company=company
        )
        
        # Filtros opcionales
        primary_product_id = self.request.query_params.get('primary_product_id')
        support_min = self.request.query_params.get('support_min')
        confidence_min = self.request.query_params.get('confidence_min')
        
        if primary_product_id:
            queryset = queryset.filter(primary_product_id=primary_product_id)
        if support_min:
            queryset = queryset.filter(support__gte=float(support_min))
        if confidence_min:
            queryset = queryset.filter(confidence__gte=float(confidence_min))
            
        return queryset.order_by('-confidence', '-support')
    
    @action(detail=False, methods=['post'])
    def analyze_basket(self, request):
        """Realiza análisis de market basket"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer_service = CustomerIntelligenceService()
            basket_analysis = customer_service.market_basket_analysis(
                company=company,
                **request.data
            )
            
            serializer = self.get_serializer(basket_analysis, many=True)
            return Response({
                'success': True,
                'basket_analysis': serializer.data,
                'count': len(basket_analysis)
            })
            
        except Exception as e:
            logger.error(f"Error en market basket analysis: {str(e)}")
            return Response({
                'error': 'Error al analizar market basket',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerBehaviorPatternViewSet(viewsets.ModelViewSet):
    """ViewSet para patrones de comportamiento de clientes"""
    serializer_class = CustomerBehaviorPatternSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return CustomerBehaviorPattern.objects.none()
        
        # Filtrar por clientes de la empresa
        queryset = CustomerBehaviorPattern.objects.select_related('customer').filter(
            customer__in=Customer.objects.filter(company=company)
        )
        
        # Filtros opcionales
        customer_id = self.request.query_params.get('customer_id')
        pattern_type = self.request.query_params.get('pattern_type')
        behavior_category = self.request.query_params.get('behavior_category')
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if pattern_type:
            queryset = queryset.filter(pattern_type=pattern_type)
        if behavior_category:
            queryset = queryset.filter(behavior_category=behavior_category)
            
        return queryset.order_by('-analysis_date')


class PriceOptimizationViewSet(viewsets.ModelViewSet):
    """ViewSet para optimización de precios"""
    serializer_class = PriceOptimizationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return PriceOptimization.objects.none()
        
        queryset = PriceOptimization.objects.select_related('product').filter(
            product__company=company
        )
        
        # Filtros opcionales
        product_id = self.request.query_params.get('product_id')
        optimization_type = self.request.query_params.get('optimization_type')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if optimization_type:
            queryset = queryset.filter(optimization_type=optimization_type)
            
        return queryset.order_by('-analysis_date')
    
    @action(detail=False, methods=['post'])
    def optimize_prices(self, request):
        """Optimiza precios de productos"""
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer_service = CustomerIntelligenceService()
            price_optimization = customer_service.optimize_product_prices(
                company=company,
                **request.data
            )
            
            serializer = self.get_serializer(price_optimization, many=True)
            return Response({
                'success': True,
                'price_optimization': serializer.data,
                'count': len(price_optimization)
            })
            
        except Exception as e:
            logger.error(f"Error optimizando precios: {str(e)}")
            return Response({
                'error': 'Error al optimizar precios',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CrossSellModelViewSet(viewsets.ModelViewSet):
    """ViewSet para modelos de cross-sell"""
    serializer_class = CrossSellModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return CrossSellModel.objects.none()
        
        # Filtrar por productos de la empresa
        queryset = CrossSellModel.objects.select_related(
            'product', 'recommended_product'
        ).filter(
            product__company=company
        )
        
        # Filtros opcionales
        product_id = self.request.query_params.get('product_id')
        recommendation_score_min = self.request.query_params.get('recommendation_score_min')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if recommendation_score_min:
            queryset = queryset.filter(
                recommendation_score__gte=float(recommendation_score_min)
            )
            
        return queryset.order_by('-recommendation_score')


class CustomerSatisfactionModelViewSet(viewsets.ModelViewSet):
    """ViewSet para modelos de satisfacción del cliente"""
    serializer_class = CustomerSatisfactionModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return CustomerSatisfactionModel.objects.none()
        
        # Filtrar por clientes de la empresa
        queryset = CustomerSatisfactionModel.objects.select_related('customer').filter(
            customer__in=Customer.objects.filter(company=company)
        )
        
        # Filtros opcionales
        customer_id = self.request.query_params.get('customer_id')
        satisfaction_score_min = self.request.query_params.get('satisfaction_score_min')
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if satisfaction_score_min:
            queryset = queryset.filter(
                satisfaction_score__gte=float(satisfaction_score_min)
            )
            
        return queryset.order_by('-analysis_date')


class LoyaltyProgramModelViewSet(viewsets.ModelViewSet):
    """ViewSet para modelos de programa de lealtad"""
    serializer_class = LoyaltyProgramModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return LoyaltyProgramModel.objects.none()
        
        # Filtrar por clientes de la empresa
        queryset = LoyaltyProgramModel.objects.select_related('customer').filter(
            customer__in=Customer.objects.filter(company=company)
        )
        
        # Filtros opcionales
        customer_id = self.request.query_params.get('customer_id')
        loyalty_tier = self.request.query_params.get('loyalty_tier')
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if loyalty_tier:
            queryset = queryset.filter(loyalty_tier=loyalty_tier)
            
        return queryset.order_by('-analysis_date')


class CustomerEngagementModelViewSet(viewsets.ModelViewSet):
    """ViewSet para modelos de engagement de clientes"""
    serializer_class = CustomerEngagementModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ForecastPagination
    
    def get_queryset(self):
        company = get_user_company(self.request)
        if not company:
            return CustomerEngagementModel.objects.none()
        
        # Filtrar por clientes de la empresa
        queryset = CustomerEngagementModel.objects.select_related('customer').filter(
            customer__in=Customer.objects.filter(company=company)
        )
        
        # Filtros opcionales
        customer_id = self.request.query_params.get('customer_id')
        engagement_level = self.request.query_params.get('engagement_level')
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if engagement_level:
            queryset = queryset.filter(engagement_level=engagement_level)
            
        return queryset.order_by('-analysis_date')


class CustomerIntelligenceView(APIView):
    """Vista para inteligencia completa de clientes"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer_service = CustomerIntelligenceService()
            intelligence = customer_service.comprehensive_customer_intelligence(
                company=company,
                **request.data
            )
            
            return Response({
                'success': True,
                'customer_intelligence': intelligence,
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error en customer intelligence: {str(e)}")
            return Response({
                'error': 'Error al generar customer intelligence',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerDashboardView(APIView):
    """Vista para dashboard de clientes con métricas clave"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company = get_user_company(request)
        if not company:
            return Response({'error': 'No company found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer_service = CustomerIntelligenceService()
            dashboard_data = customer_service.get_customer_dashboard(company)
            
            return Response({
                'success': True,
                'dashboard': dashboard_data,
                'generated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error generando dashboard de clientes: {str(e)}")
            return Response({
                'error': 'Error al generar dashboard de clientes',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


__all__ = [
    'CustomerLifetimeValueViewSet',
    'ChurnPredictionViewSet',
    'CustomerSegmentationViewSet',
    'MarketBasketAnalysisViewSet',
    'CustomerBehaviorPatternViewSet',
    'PriceOptimizationViewSet',
    'CrossSellModelViewSet',
    'CustomerSatisfactionModelViewSet',
    'LoyaltyProgramModelViewSet',
    'CustomerEngagementModelViewSet',
    'CustomerIntelligenceView',
    'CustomerDashboardView'
]
