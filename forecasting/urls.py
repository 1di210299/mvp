from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Forecasting principal
    ForecastModelViewSet, DemandForecastViewSet, ReorderRecommendationViewSet,
    PredictDemandView, TrainModelView, ModelComparisonView, ModelPerformanceView,
    ForecastChartView, ProductForecastSummaryView,
    
    # Financial views
    FinancialForecastModelViewSet, RevenuePredictionViewSet, CashFlowForecastViewSet,
    ProfitabilityAnalysisViewSet, FinancialRiskAssessmentViewSet, SeasonalityAnalysisViewSet,
    CostOptimizationModelViewSet, RevenueBreakdownViewSet, FinancialScenarioViewSet,
    ProfitMarginAnalysisViewSet, FinancialTrendAnalysisViewSet,
    FinancialDashboardView, FinancialReportView,
    
    # Demand & Inventory views
    DemandPatternViewSet, AdvancedDemandForecastViewSet, SeasonalPatternViewSet,
    InventoryOptimizationModelViewSet, StockLevelRecommendationViewSet,
    SupplierPerformanceModelViewSet, ProcurementOptimizationViewSet,
    SupplierRiskAnalysisViewSet, SupplierROIAnalysisViewSet,
    InventoryTurnoverAnalysisViewSet, DemandAnalysisView, InventoryOptimizationView,
    
    # Customer Intelligence views
    CustomerLifetimeValueViewSet, ChurnPredictionViewSet, CustomerSegmentationViewSet,
    MarketBasketAnalysisViewSet, CustomerBehaviorPatternViewSet, PriceOptimizationViewSet,
    CrossSellModelViewSet, CustomerSatisfactionModelViewSet, LoyaltyProgramModelViewSet,
    CustomerEngagementModelViewSet, CustomerIntelligenceView, CustomerDashboardView
)

router = DefaultRouter()

# ===== FORECASTING PRINCIPAL =====
router.register(r'models', ForecastModelViewSet, basename='forecastmodel')
router.register(r'forecasts', DemandForecastViewSet, basename='demandforecast')
router.register(r'reorder-recommendations', ReorderRecommendationViewSet, basename='reorderrecommendation')

# ===== FINANCIAL FORECASTING =====
router.register(r'financial/models', FinancialForecastModelViewSet, basename='financial-models')
router.register(r'financial/revenue-predictions', RevenuePredictionViewSet, basename='revenue-predictions')
router.register(r'financial/cash-flow', CashFlowForecastViewSet, basename='cash-flow')
router.register(r'financial/profitability', ProfitabilityAnalysisViewSet, basename='profitability')
router.register(r'financial/risk-assessment', FinancialRiskAssessmentViewSet, basename='risk-assessment')
router.register(r'financial/seasonality', SeasonalityAnalysisViewSet, basename='seasonality')
router.register(r'financial/cost-optimization', CostOptimizationModelViewSet, basename='cost-optimization')
router.register(r'financial/revenue-breakdown', RevenueBreakdownViewSet, basename='revenue-breakdown')
router.register(r'financial/scenarios', FinancialScenarioViewSet, basename='financial-scenarios')
router.register(r'financial/profit-margins', ProfitMarginAnalysisViewSet, basename='profit-margins')
router.register(r'financial/trends', FinancialTrendAnalysisViewSet, basename='financial-trends')

# ===== DEMAND ANALYSIS & INVENTORY OPTIMIZATION =====
router.register(r'demand/patterns', DemandPatternViewSet, basename='demand-patterns')
router.register(r'demand/advanced-forecasts', AdvancedDemandForecastViewSet, basename='advanced-forecasts')
router.register(r'demand/seasonal-patterns', SeasonalPatternViewSet, basename='seasonal-patterns')
router.register(r'inventory/optimization-models', InventoryOptimizationModelViewSet, basename='inventory-models')
router.register(r'inventory/stock-recommendations', StockLevelRecommendationViewSet, basename='stock-recommendations')
router.register(r'suppliers/performance', SupplierPerformanceModelViewSet, basename='supplier-performance')
router.register(r'suppliers/procurement', ProcurementOptimizationViewSet, basename='procurement')
router.register(r'suppliers/risk-analysis', SupplierRiskAnalysisViewSet, basename='supplier-risk')
router.register(r'suppliers/roi-analysis', SupplierROIAnalysisViewSet, basename='supplier-roi')
router.register(r'inventory/turnover', InventoryTurnoverAnalysisViewSet, basename='inventory-turnover')

# ===== CUSTOMER INTELLIGENCE =====
router.register(r'customers/lifetime-value', CustomerLifetimeValueViewSet, basename='customer-clv')
router.register(r'customers/churn-prediction', ChurnPredictionViewSet, basename='churn-prediction')
router.register(r'customers/segmentation', CustomerSegmentationViewSet, basename='customer-segmentation')
router.register(r'customers/market-basket', MarketBasketAnalysisViewSet, basename='market-basket')
router.register(r'customers/behavior-patterns', CustomerBehaviorPatternViewSet, basename='behavior-patterns')
router.register(r'customers/price-optimization', PriceOptimizationViewSet, basename='price-optimization')
router.register(r'customers/cross-sell', CrossSellModelViewSet, basename='cross-sell')
router.register(r'customers/satisfaction', CustomerSatisfactionModelViewSet, basename='customer-satisfaction')
router.register(r'customers/loyalty-program', LoyaltyProgramModelViewSet, basename='loyalty-program')
router.register(r'customers/engagement', CustomerEngagementModelViewSet, basename='customer-engagement')

urlpatterns = [
    # ===== FORECASTING PRINCIPAL =====
    # ML Model Management
    path('predict/', PredictDemandView.as_view(), name='predict_demand'),
    path('train-model/', TrainModelView.as_view(), name='train_model'),
    path('models/comparison/', ModelComparisonView.as_view(), name='model_comparison'),
    path('model-performance/', ModelPerformanceView.as_view(), name='model_performance'),
    
    # Gráficos y reportes
    path('charts/', ForecastChartView.as_view(), name='forecast-chart'),
    path('summary/', ProductForecastSummaryView.as_view(), name='forecast-summary'),

    # ===== ANÁLISIS INTEGRALES AVANZADOS =====
    # Financial Analysis
    path('financial/dashboard/', FinancialDashboardView.as_view(), name='financial-dashboard'),
    path('financial/reports/', FinancialReportView.as_view(), name='financial-reports'),
    
    # Demand & Inventory Analysis
    path('demand/analysis/', DemandAnalysisView.as_view(), name='demand-analysis'),
    path('inventory/optimization/', InventoryOptimizationView.as_view(), name='inventory-optimization'),
    
    # Customer Intelligence
    path('customers/intelligence/', CustomerIntelligenceView.as_view(), name='customer-intelligence'),
    path('customers/dashboard/', CustomerDashboardView.as_view(), name='customer-dashboard'),

    # ===== VIEWSETS (CRUD OPERATIONS) =====
    path('', include(router.urls)),
]
