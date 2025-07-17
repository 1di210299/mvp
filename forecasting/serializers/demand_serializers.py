"""
Serializers para modelos de demanda e inventario
"""

from rest_framework import serializers
from ..models import (
    DemandPattern, AdvancedDemandForecast, SeasonalPattern,
    InventoryOptimizationModel, StockLevelRecommendation,
    SupplierPerformanceModel, ProcurementOptimization,
    SupplierRiskAnalysis, InventoryTurnoverAnalysis,
    DemandPatternAnalysis, TrendingProductPrediction,
    OptimalStockLevel, StockoutPrediction
)


class DemandPatternSerializer(serializers.ModelSerializer):
    """Serializer para patrones de demanda"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = DemandPattern
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class AdvancedDemandForecastSerializer(serializers.ModelSerializer):
    """Serializer para pronósticos avanzados de demanda"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = AdvancedDemandForecast
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class SeasonalPatternSerializer(serializers.ModelSerializer):
    """Serializer para patrones estacionales"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SeasonalPattern
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class InventoryOptimizationModelSerializer(serializers.ModelSerializer):
    """Serializer para modelos de optimización de inventario"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = InventoryOptimizationModel
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class StockLevelRecommendationSerializer(serializers.ModelSerializer):
    """Serializer para recomendaciones de nivel de stock"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    model_name = serializers.CharField(source='model.company.name', read_only=True)
    
    class Meta:
        model = StockLevelRecommendation
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class SupplierPerformanceModelSerializer(serializers.ModelSerializer):
    """Serializer para modelos de rendimiento de proveedores"""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = SupplierPerformanceModel
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class ProcurementOptimizationSerializer(serializers.ModelSerializer):
    """Serializer para optimización de procuramiento"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    cost_savings_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcurementOptimization
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_cost_savings_formatted(self, obj):
        return f"S/ {obj.cost_savings:,.2f}"


class SupplierRiskAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis de riesgo de proveedores"""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = SupplierRiskAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class InventoryTurnoverAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis de rotación de inventario"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = InventoryTurnoverAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class DemandPatternAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis de patrones de demanda"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    seasonality_strength_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = DemandPatternAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_seasonality_strength_percentage(self, obj):
        """Formatear fuerza de estacionalidad como porcentaje"""
        return f"{obj.seasonality_strength:.1f}%"


class TrendingProductPredictionSerializer(serializers.ModelSerializer):
    """Serializer para predicción de productos en tendencia"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    category_name = serializers.CharField(source='product.category.name', read_only=True)
    growth_rate_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = TrendingProductPrediction
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_growth_rate_percentage(self, obj):
        """Formatear tasa de crecimiento como porcentaje"""
        return f"{obj.predicted_growth_rate:.1f}%"


class OptimalStockLevelSerializer(serializers.ModelSerializer):
    """Serializer para niveles óptimos de stock"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    current_stock = serializers.CharField(source='product.stock_quantity', read_only=True)
    stock_status = serializers.SerializerMethodField()
    
    class Meta:
        model = OptimalStockLevel
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_stock_status(self, obj):
        """Determinar status del stock actual vs óptimo"""
        current = float(obj.product.stock_quantity or 0)
        optimal = float(obj.optimal_quantity)
        
        if current < optimal * 0.8:
            return "BAJO - Reabastecer pronto"
        elif current > optimal * 1.2:
            return "ALTO - Considerar reducir"
        else:
            return "ÓPTIMO - En rango adecuado"


class StockoutPredictionSerializer(serializers.ModelSerializer):
    """Serializer para predicción de agotamientos"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    current_stock = serializers.CharField(source='product.stock_quantity', read_only=True)
    risk_level_text = serializers.SerializerMethodField()
    days_until_stockout_text = serializers.SerializerMethodField()
    
    class Meta:
        model = StockoutPrediction
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_risk_level_text(self, obj):
        """Texto explicativo del nivel de riesgo"""
        risk = float(obj.stockout_probability)
        
        if risk >= 0.8:
            return "CRÍTICO - Acción inmediata requerida"
        elif risk >= 0.6:
            return "ALTO - Reabastecer pronto"
        elif risk >= 0.4:
            return "MEDIO - Monitorear de cerca"
        else:
            return "BAJO - Stock suficiente"
    
    def get_days_until_stockout_text(self, obj):
        """Texto explicativo de días hasta agotamiento"""
        days = obj.days_until_stockout
        
        if days <= 7:
            return f"URGENTE: {days} días restantes"
        elif days <= 30:
            return f"PRONTO: {days} días restantes"
        else:
            return f"SUFICIENTE: {days} días restantes"
