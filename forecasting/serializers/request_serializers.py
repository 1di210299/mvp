"""
Serializers para requests y datos de entrada
"""

from rest_framework import serializers


class TrainModelRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de entrenamiento de modelos"""
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="IDs de productos para entrenar. Si no se especifica, entrena todos los productos activos."
    )
    model_type = serializers.ChoiceField(
        choices=['prophet', 'arima', 'linear_regression', 'random_forest', 'lstm'],
        default='prophet',
        help_text="Tipo de modelo a usar para el entrenamiento"
    )
    forecast_horizon_days = serializers.IntegerField(
        default=30,
        min_value=1,
        max_value=365,
        help_text="Días hacia el futuro para el pronóstico"
    )
    training_period_days = serializers.IntegerField(
        default=365,
        min_value=30,
        max_value=1095,
        help_text="Días de datos históricos para entrenar"
    )
    retrain_existing = serializers.BooleanField(
        default=False,
        help_text="Si re-entrenar modelos existentes"
    )
    async_training = serializers.BooleanField(
        default=True,
        help_text="Si ejecutar el entrenamiento en segundo plano"
    )


class PredictDemandRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de predicción"""
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="IDs de productos para predecir. Si no se especifica, predice todos los productos con modelos."
    )
    forecast_horizon = serializers.IntegerField(
        default=30,
        min_value=1,
        max_value=365,
        help_text="Días hacia el futuro para predecir"
    )
    include_confidence_intervals = serializers.BooleanField(
        default=True,
        help_text="Si incluir intervalos de confianza en las predicciones"
    )


class ModelComparisonSerializer(serializers.Serializer):
    """Serializer para respuestas de comparación de modelos"""
    model_id = serializers.IntegerField()
    model_name = serializers.CharField()
    model_type = serializers.CharField()
    product_name = serializers.CharField()
    accuracy_metrics = serializers.DictField()
    training_time = serializers.FloatField(required=False)
    last_trained = serializers.DateTimeField()


class ForecastChartDataSerializer(serializers.Serializer):
    """Serializer para datos de gráficos de pronósticos"""
    dates = serializers.ListField(child=serializers.DateField())
    historical_demand = serializers.ListField(child=serializers.FloatField())
    predicted_demand = serializers.ListField(child=serializers.FloatField())
    confidence_lower = serializers.ListField(child=serializers.FloatField(), required=False)
    confidence_upper = serializers.ListField(child=serializers.FloatField(), required=False)
    model_name = serializers.CharField()
    product_name = serializers.CharField()


class RevenueforecastRequestSerializer(serializers.Serializer):
    """Serializer para request de pronóstico de ingresos"""
    company_id = serializers.IntegerField()
    time_horizon = serializers.IntegerField(default=12, min_value=1, max_value=60)
    include_seasonality = serializers.BooleanField(default=True)


class SupplierROIRequestSerializer(serializers.Serializer):
    """Serializer para request de análisis ROI"""
    company_id = serializers.IntegerField(required=False)
    supplier_id = serializers.IntegerField(required=False)
    time_period = serializers.IntegerField(default=12, min_value=3, max_value=36)


class CashFlowRequestSerializer(serializers.Serializer):
    """Serializer para request de predicción de flujo de caja"""
    company_id = serializers.IntegerField()
    forecast_months = serializers.IntegerField(default=6, min_value=1, max_value=24)
    include_scenarios = serializers.BooleanField(default=True)


class SeasonalPatternsRequestSerializer(serializers.Serializer):
    """Serializer para request de patrones estacionales"""
    company_id = serializers.IntegerField()
    product_id = serializers.IntegerField(required=False)
    category_id = serializers.IntegerField(required=False)
    years_history = serializers.IntegerField(default=2, min_value=1, max_value=5)


class MarketBasketRequestSerializer(serializers.Serializer):
    """Serializer para request de market basket analysis"""
    company_id = serializers.IntegerField()
    min_support = serializers.FloatField(default=0.01, min_value=0.001, max_value=0.5)
    min_confidence = serializers.FloatField(default=0.3, min_value=0.1, max_value=0.9)
    time_period = serializers.IntegerField(default=6, min_value=1, max_value=24)


class PriceElasticityRequestSerializer(serializers.Serializer):
    """Serializer para request de elasticidad de precios"""
    product_id = serializers.IntegerField()
    time_period = serializers.IntegerField(default=12, min_value=3, max_value=36)


class OptimalStockRequestSerializer(serializers.Serializer):
    """Serializer para request de stock óptimo"""
    company_id = serializers.IntegerField(required=False)
    product_id = serializers.IntegerField(required=False)
    service_level = serializers.FloatField(default=0.95, min_value=0.8, max_value=0.99)
    lead_time_days = serializers.IntegerField(default=7, min_value=1, max_value=90)


class StockoutPredictionRequestSerializer(serializers.Serializer):
    """Serializer para request de predicción de agotamientos"""
    company_id = serializers.IntegerField()
    days_ahead = serializers.IntegerField(default=30, min_value=7, max_value=365)
    risk_threshold = serializers.FloatField(default=0.7, min_value=0.1, max_value=0.9)


class CustomerCLVRequestSerializer(serializers.Serializer):
    """Serializer para request de CLV"""
    customer_id = serializers.IntegerField(required=False)
    company_id = serializers.IntegerField(required=False)


class CustomerChurnRequestSerializer(serializers.Serializer):
    """Serializer para request de análisis de churn"""
    customer_id = serializers.IntegerField(required=False)
    company_id = serializers.IntegerField(required=False)
    risk_threshold = serializers.FloatField(default=0.6, min_value=0.1, max_value=0.9)


class NextPurchaseRequestSerializer(serializers.Serializer):
    """Serializer para request de predicción de próxima compra"""
    customer_id = serializers.IntegerField()


class CustomerSegmentationRequestSerializer(serializers.Serializer):
    """Serializer para request de segmentación de clientes"""
    company_id = serializers.IntegerField()
    min_transactions = serializers.IntegerField(default=2, min_value=1, max_value=10)
