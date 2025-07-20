"""
Estructura modular de vistas para forecasting
"""

# Importar funciones de base
from .base_views import ForecastPagination, get_user_company

# Importar todas las vistas de forecasting principal
from .forecast_views import (
    ForecastModelViewSet, DemandForecastViewSet, ReorderRecommendationViewSet,
    PredictDemandView, TrainModelView, ModelComparisonView, ModelPerformanceView,
    ForecastChartView, ProductForecastSummaryView
)

# Importar todas las vistas financieras
from .financial_views import (
    FinancialForecastModelViewSet, RevenuePredictionViewSet, CashFlowForecastViewSet,
    ProfitabilityAnalysisViewSet, FinancialRiskAssessmentViewSet, SeasonalityAnalysisViewSet,
    CostOptimizationModelViewSet, RevenueBreakdownViewSet, FinancialScenarioViewSet,
    ProfitMarginAnalysisViewSet, FinancialTrendAnalysisViewSet,
    FinancialDashboardView, FinancialReportView
)

# Importar todas las vistas de demanda e inventario
from .demand_views import (
    DemandPatternViewSet, AdvancedDemandForecastViewSet, SeasonalPatternViewSet,
    InventoryOptimizationModelViewSet, StockLevelRecommendationViewSet,
    SupplierPerformanceModelViewSet, ProcurementOptimizationViewSet,
    SupplierRiskAnalysisViewSet, SupplierROIAnalysisViewSet,
    InventoryTurnoverAnalysisViewSet, DemandAnalysisView, InventoryOptimizationView
)

# Importar todas las vistas de customer intelligence
from .customer_views import (
    CustomerLifetimeValueViewSet, ChurnPredictionViewSet, CustomerSegmentationViewSet,
    MarketBasketAnalysisViewSet, CustomerBehaviorPatternViewSet, PriceOptimizationViewSet,
    CrossSellModelViewSet, CustomerSatisfactionModelViewSet, LoyaltyProgramModelViewSet,
    CustomerEngagementModelViewSet, CustomerIntelligenceView, CustomerDashboardView
)

__all__ = [
    # Base
    'ForecastPagination',
    'get_user_company',
    
    # Forecasting principal
    'ForecastModelViewSet',
    'DemandForecastViewSet',
    'ReorderRecommendationViewSet',
    'PredictDemandView',
    'TrainModelView',
    'ModelComparisonView',
    'ModelPerformanceView',
    'ForecastChartView',
    'ProductForecastSummaryView',
    
    # Vistas financieras
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
    'FinancialReportView',
    
    # Vistas de demanda e inventario
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
    'InventoryOptimizationView',
    
    # Vistas de customer intelligence
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
