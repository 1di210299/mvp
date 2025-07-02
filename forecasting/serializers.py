from rest_framework import serializers
from .models import ForecastModel, DemandForecast, ReorderRecommendation
from inventory.models import Product


class ForecastModelSerializer(serializers.ModelSerializer):
    algorithm_display = serializers.CharField(source='get_algorithm_display', read_only=True)
    accuracy_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ForecastModel
        fields = [
            'id', 'name', 'algorithm', 'algorithm_display', 'product', 
            'parameters', 'accuracy_metrics', 'accuracy_percentage',
            'is_active', 'created_at', 'updated_at', 'last_trained_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_trained_at', 'accuracy_metrics']
    
    def get_accuracy_percentage(self, obj):
        """Obtiene el porcentaje de precisión del modelo"""
        if obj.accuracy_metrics:
            mape = obj.accuracy_metrics.get('mape')
            if mape is not None:
                return max(0, 100 - mape)
        return None


class DemandForecastSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    confidence_interval_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DemandForecast
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'model', 'model_name',
            'forecast_date', 'forecast_horizon_days', 'predicted_demand',
            'confidence_interval', 'confidence_interval_display', 'accuracy_score',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_confidence_interval_display(self, obj):
        """Formato legible del intervalo de confianza"""
        if obj.confidence_interval:
            lower = obj.confidence_interval.get('lower', 0)
            upper = obj.confidence_interval.get('upper', 0)
            return f"{lower:.2f} - {upper:.2f}"
        return None


class ReorderRecommendationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    
    class Meta:
        model = ReorderRecommendation
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'current_stock',
            'recommended_order_quantity', 'urgency', 'urgency_display',
            'estimated_stockout_date', 'reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TrainModelRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de entrenamiento de modelos"""
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="IDs de productos para entrenar. Si no se especifica, entrena todos los productos activos."
    )
    algorithm = serializers.ChoiceField(
        choices=['prophet', 'arima', 'ensemble'],
        default='ensemble',
        help_text="Algoritmo a usar para el entrenamiento"
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
    algorithm = serializers.CharField()
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


class ProductForecastSummarySerializer(serializers.Serializer):
    """Serializer para resumen de pronósticos por producto"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    current_stock = serializers.FloatField()
    forecasts = DemandForecastSerializer(many=True)
    recommendations = ReorderRecommendationSerializer(many=True)
    best_model = ForecastModelSerializer(required=False)
