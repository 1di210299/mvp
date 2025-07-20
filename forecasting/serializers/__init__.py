"""
Paquete de serializers para forecasting
"""

# Serializers básicos
from .base_serializers import (
    ForecastModelSerializer,
    DemandForecastSerializer,
    ForecastAccuracySerializer,
    ReorderRecommendationSerializer,
    ModelTrainingJobSerializer,
    ProductForecastSummarySerializer,
)

# Serializers de request/input
from .request_serializers import (
    TrainModelRequestSerializer,
    PredictDemandRequestSerializer,
    ModelComparisonSerializer,
    ForecastChartDataSerializer,
    ModelPerformanceResponseSerializer,
    ModelPerformanceListResponseSerializer,
    OverallPerformanceMetricsSerializer,
    RevenueforecastRequestSerializer,
    SupplierROIRequestSerializer,
    CashFlowRequestSerializer,
    SeasonalPatternsRequestSerializer,
    MarketBasketRequestSerializer,
    PriceElasticityRequestSerializer,
    OptimalStockRequestSerializer,
    StockoutPredictionRequestSerializer,
    CustomerCLVRequestSerializer,
    CustomerChurnRequestSerializer,
    NextPurchaseRequestSerializer,
    CustomerSegmentationRequestSerializer,
)

# Serializers financieros
from .financial_serializers import (
    FinancialForecastModelSerializer,
    RevenuePredictionSerializer,
    CashFlowForecastSerializer,
    ProfitabilityAnalysisSerializer,
    FinancialRiskAssessmentSerializer,
    SeasonalityAnalysisSerializer,
    CostOptimizationModelSerializer,
    RevenueBreakdownSerializer,
    FinancialScenarioSerializer,
    ProfitMarginAnalysisSerializer,
    FinancialTrendAnalysisSerializer,
)

# Serializers de demanda e inventario
from .demand_serializers import (
    DemandPatternSerializer,
    AdvancedDemandForecastSerializer,
    SeasonalPatternSerializer,
    InventoryOptimizationModelSerializer,
    StockLevelRecommendationSerializer,
    SupplierPerformanceModelSerializer,
    ProcurementOptimizationSerializer,
    SupplierRiskAnalysisSerializer,
    InventoryTurnoverAnalysisSerializer,
    DemandPatternAnalysisSerializer,
    TrendingProductPredictionSerializer,
    OptimalStockLevelSerializer,
    StockoutPredictionSerializer,
)

# Serializers de customer intelligence
from .customer_serializers import (
    CustomerBehaviorPatternSerializer,
    PriceOptimizationSerializer,
    CrossSellModelSerializer,
    CustomerSatisfactionModelSerializer,
    LoyaltyProgramModelSerializer,
    CustomerEngagementModelSerializer,
    CustomerLifetimeValueSerializer,
    ChurnPredictionSerializer,
    NextPurchasePredictionSerializer,
    ProductRecommendationSerializer,
    CustomerSegmentationSerializer,
)

# Serializers de análisis y insights
from .analysis_serializers import (
    SupplierROIAnalysisSerializer,
    MarketBasketAnalysisSerializer,
    PriceElasticityAnalysisSerializer,
)

__all__ = [
    # Base serializers
    'ForecastModelSerializer',
    'DemandForecastSerializer',
    'ForecastAccuracySerializer',
    'ReorderRecommendationSerializer',
    'ModelTrainingJobSerializer',
    'ProductForecastSummarySerializer',
    
    # Request serializers
    'TrainModelRequestSerializer',
    'PredictDemandRequestSerializer',
    'ModelComparisonSerializer',
    'ForecastChartDataSerializer',
    'ModelPerformanceResponseSerializer',
    'ModelPerformanceListResponseSerializer',
    'OverallPerformanceMetricsSerializer',
    'RevenueforecastRequestSerializer',
    'SupplierROIRequestSerializer',
    'CashFlowRequestSerializer',
    'SeasonalPatternsRequestSerializer',
    'MarketBasketRequestSerializer',
    'PriceElasticityRequestSerializer',
    'OptimalStockRequestSerializer',
    'StockoutPredictionRequestSerializer',
    'CustomerCLVRequestSerializer',
    'CustomerChurnRequestSerializer',
    'NextPurchaseRequestSerializer',
    'CustomerSegmentationRequestSerializer',
    
    # Financial serializers
    'FinancialForecastModelSerializer',
    'RevenuePredictionSerializer',
    'CashFlowForecastSerializer',
    'ProfitabilityAnalysisSerializer',
    'FinancialRiskAssessmentSerializer',
    'SeasonalityAnalysisSerializer',
    'CostOptimizationModelSerializer',
    'RevenueBreakdownSerializer',
    'FinancialScenarioSerializer',
    'ProfitMarginAnalysisSerializer',
    'FinancialTrendAnalysisSerializer',
    
    # Demand serializers
    'DemandPatternSerializer',
    'AdvancedDemandForecastSerializer',
    'SeasonalPatternSerializer',
    'InventoryOptimizationModelSerializer',
    'StockLevelRecommendationSerializer',
    'SupplierPerformanceModelSerializer',
    'ProcurementOptimizationSerializer',
    'SupplierRiskAnalysisSerializer',
    'InventoryTurnoverAnalysisSerializer',
    'DemandPatternAnalysisSerializer',
    'TrendingProductPredictionSerializer',
    'OptimalStockLevelSerializer',
    'StockoutPredictionSerializer',
    
    # Customer serializers
    'CustomerBehaviorPatternSerializer',
    'PriceOptimizationSerializer',
    'CrossSellModelSerializer',
    'CustomerSatisfactionModelSerializer',
    'LoyaltyProgramModelSerializer',
    'CustomerEngagementModelSerializer',
    'CustomerLifetimeValueSerializer',
    'ChurnPredictionSerializer',
    'NextPurchasePredictionSerializer',
    'ProductRecommendationSerializer',
    'CustomerSegmentationSerializer',
    
    # Analysis serializers
    'SupplierROIAnalysisSerializer',
    'MarketBasketAnalysisSerializer',
    'PriceElasticityAnalysisSerializer',
]
