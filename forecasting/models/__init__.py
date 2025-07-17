"""
Modelos de forecasting organizados por categoría
"""

# Modelos base de forecasting
from .base_models import (
    ForecastModel, DemandForecast, ForecastAccuracy, 
    ReorderRecommendation, ModelTrainingJob
)

# Modelos financieros avanzados
from .financial_models import (
    RevenueForecasting, FinancialForecastModel, RevenuePrediction,
    CashFlowForecast, ProfitabilityAnalysis, FinancialRiskAssessment,
    SeasonalityAnalysis, CostOptimizationModel, RevenueBreakdown,
    FinancialScenario, ProfitMarginAnalysis, FinancialTrendAnalysis
)

# Modelos de demanda e inventario
from .demand_models import (
    DemandPattern, AdvancedDemandForecast, SeasonalPattern,
    InventoryOptimizationModel, StockLevelRecommendation,
    SupplierPerformanceModel, ProcurementOptimization,
    SupplierRiskAnalysis, InventoryTurnoverAnalysis,
    DemandPatternAnalysis, PriceElasticity, SeasonalityPattern,
    OptimalStockLevel
)

# Modelos de customer intelligence
from .customer_models import (
    CustomerLifetimeValue, ChurnPrediction, CustomerSegmentation,
    NextPurchasePrediction, ProductRecommendation, MarketBasketAnalysis,
    CustomerBehaviorPattern, PriceOptimization, CrossSellModel,
    CustomerSatisfactionModel, LoyaltyProgramModel, CustomerEngagementModel
)

# Modelos de análisis avanzado
from .analysis_models import (
    SupplierROIAnalysis, PriceElasticityAnalysis, TrendingProductPrediction,
    StockoutPrediction
)

# Exportar todos los modelos para mantener compatibilidad
__all__ = [
    # Base models
    'ForecastModel', 'DemandForecast', 'ForecastAccuracy', 
    'ReorderRecommendation', 'ModelTrainingJob',
    
    # Financial models
    'RevenueForecasting', 'FinancialForecastModel', 'RevenuePrediction',
    'CashFlowForecast', 'ProfitabilityAnalysis', 'FinancialRiskAssessment',
    'SeasonalityAnalysis', 'CostOptimizationModel', 'RevenueBreakdown',
    'FinancialScenario', 'ProfitMarginAnalysis', 'FinancialTrendAnalysis',
    
    # Demand models
    'DemandPattern', 'AdvancedDemandForecast', 'SeasonalPattern',
    'InventoryOptimizationModel', 'StockLevelRecommendation',
    'SupplierPerformanceModel', 'ProcurementOptimization',
    'SupplierRiskAnalysis', 'InventoryTurnoverAnalysis',
    'DemandPatternAnalysis', 'PriceElasticity', 'SeasonalityPattern',
    'OptimalStockLevel',
    
    # Customer models
    'CustomerLifetimeValue', 'ChurnPrediction', 'CustomerSegmentation',
    'NextPurchasePrediction', 'ProductRecommendation', 'MarketBasketAnalysis',
    'CustomerBehaviorPattern', 'PriceOptimization', 'CrossSellModel',
    'CustomerSatisfactionModel', 'LoyaltyProgramModel', 'CustomerEngagementModel',
    
    # Analysis models
    'SupplierROIAnalysis', 'PriceElasticityAnalysis', 'TrendingProductPrediction',
    'StockoutPrediction',
]
