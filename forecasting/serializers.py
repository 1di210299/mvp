from rest_framework import serializers
from .models import ForecastModel, DemandForecast, ReorderRecommendation, ModelTrainingJob, ForecastAccuracy
from inventory.models import Product


class ForecastModelSerializer(serializers.ModelSerializer):
    model_type_display = serializers.CharField(source='get_model_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    accuracy_percentage = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    category_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ForecastModel
        fields = [
            'id', 'name', 'description', 'model_type', 'model_type_display', 
            'status', 'status_display', 'forecast_horizon_days', 'training_period_days',
            'confidence_interval', 'hyperparameters', 'mae', 'mape', 'rmse', 'r2_score',
            'model_file_path', 'model_size_mb', 'version', 'accuracy_percentage',
            'product_count', 'category_count', 'training_started_at', 
            'training_completed_at', 'last_prediction_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'training_started_at', 
            'training_completed_at', 'last_prediction_at', 'mae', 'mape', 
            'rmse', 'r2_score', 'model_file_path', 'model_size_mb'
        ]
    
    def get_accuracy_percentage(self, obj):
        """Obtiene el porcentaje de precisión del modelo basado en MAPE"""
        return obj.accuracy_score
    
    def get_product_count(self, obj):
        """Número de productos asociados al modelo"""
        return obj.products.count()
    
    def get_category_count(self, obj):
        """Número de categorías asociadas al modelo"""
        return obj.categories.count()


class DemandForecastSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    forecast_type_display = serializers.CharField(source='get_forecast_type_display', read_only=True)
    forecast_range = serializers.ReadOnlyField()
    uncertainty_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = DemandForecast
        fields = [
            'id', 'model', 'model_name', 'product', 'product_name', 'product_sku', 
            'location', 'location_name', 'forecast_date', 'forecast_type', 'forecast_type_display',
            'predicted_demand', 'lower_bound', 'upper_bound', 'confidence_level',
            'seasonality_factor', 'trend_factor', 'external_factors', 
            'forecast_range', 'uncertainty_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ForecastAccuracySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastAccuracy
        fields = [
            'id', 'forecast', 'actual_demand', 'absolute_error', 
            'percentage_error', 'squared_error', 'within_bounds', 'bias', 'evaluated_at'
        ]
        read_only_fields = ['id', 'absolute_error', 'percentage_error', 'squared_error', 'within_bounds', 'bias', 'evaluated_at']


class ReorderRecommendationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_until_stockout = serializers.ReadOnlyField()
    is_urgent = serializers.ReadOnlyField()
    
    class Meta:
        model = ReorderRecommendation
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'location', 'location_name',
            'recommended_quantity', 'current_stock', 'projected_demand',
            'recommended_order_date', 'expected_stockout_date', 'lead_time_days',
            'priority', 'priority_display', 'status', 'status_display',
            'estimated_cost', 'potential_lost_sales', 'forecast_model',
            'notes', 'justification', 'approved_by', 'approved_at',
            'days_until_stockout', 'is_urgent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'days_until_stockout', 'is_urgent']


class ModelTrainingJobSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='model.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.ReadOnlyField()
    duration_seconds = serializers.ReadOnlyField()
    
    class Meta:
        model = ModelTrainingJob
        fields = [
            'id', 'model', 'model_name', 'status', 'status_display',
            'started_at', 'completed_at', 'metrics', 'error_message',
            'duration', 'duration_seconds', 'created_at', 'created_by'
        ]
        read_only_fields = ['id', 'duration', 'duration_seconds', 'created_at']


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


class ProductForecastSummarySerializer(serializers.Serializer):
    """Serializer para resumen de pronósticos por producto"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    current_stock = serializers.FloatField()
    forecasts = DemandForecastSerializer(many=True)
    recommendations = ReorderRecommendationSerializer(many=True)
    best_model = ForecastModelSerializer(required=False)