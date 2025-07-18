"""
Serializers para modelos de customer intelligence
"""

from rest_framework import serializers
from ..models import (
    CustomerBehaviorPattern, PriceOptimization, CrossSellModel,
    CustomerSatisfactionModel, LoyaltyProgramModel, CustomerEngagementModel,
    CustomerLifetimeValue, ChurnPrediction, NextPurchasePrediction,
    ProductRecommendation, CustomerSegmentation
)


class CustomerBehaviorPatternSerializer(serializers.ModelSerializer):
    """Serializer para patrones de comportamiento de clientes"""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = CustomerBehaviorPattern
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class PriceOptimizationSerializer(serializers.ModelSerializer):
    """Serializer para optimización de precios"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    current_price_formatted = serializers.SerializerMethodField()
    recommended_price_formatted = serializers.SerializerMethodField()
    revenue_impact_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = PriceOptimization
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_current_price_formatted(self, obj):
        return f"S/ {obj.current_price:,.2f}"
    
    def get_recommended_price_formatted(self, obj):
        return f"S/ {obj.recommended_price:,.2f}"
    
    def get_revenue_impact_formatted(self, obj):
        return f"S/ {obj.revenue_impact:,.2f}"


class CrossSellModelSerializer(serializers.ModelSerializer):
    """Serializer para modelos de cross-sell"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    recommended_product_name = serializers.CharField(source='recommended_product.name', read_only=True)
    
    class Meta:
        model = CrossSellModel
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class CustomerSatisfactionModelSerializer(serializers.ModelSerializer):
    """Serializer para modelos de satisfacción del cliente"""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = CustomerSatisfactionModel
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class LoyaltyProgramModelSerializer(serializers.ModelSerializer):
    """Serializer para modelos de programa de lealtad"""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = LoyaltyProgramModel
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class CustomerEngagementModelSerializer(serializers.ModelSerializer):
    """Serializer para modelos de engagement de clientes"""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = CustomerEngagementModel
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class CustomerLifetimeValueSerializer(serializers.ModelSerializer):
    """Serializer para Customer Lifetime Value"""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    clv_formatted = serializers.SerializerMethodField()
    confidence_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerLifetimeValue
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_clv_formatted(self, obj):
        """Formatear CLV en soles"""
        return f"S/ {obj.predicted_clv:,.2f}"
    
    def get_confidence_percentage(self, obj):
        """Formatear confidence como porcentaje"""
        return f"{obj.clv_confidence * 100:.1f}%"


class ChurnPredictionSerializer(serializers.ModelSerializer):
    """Serializer para predicción de churn"""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    churn_probability_percentage = serializers.SerializerMethodField()
    risk_level_text = serializers.SerializerMethodField()
    
    class Meta:
        model = ChurnPrediction
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_churn_probability_percentage(self, obj):
        """Formatear probabilidad como porcentaje"""
        return f"{obj.churn_probability * 100:.1f}%"
    
    def get_risk_level_text(self, obj):
        """Texto explicativo del nivel de riesgo"""
        probability = float(obj.churn_probability)
        
        if probability >= 0.8:
            return "CRÍTICO - Cliente en riesgo inmediato"
        elif probability >= 0.6:
            return "ALTO - Requiere atención urgente"
        elif probability >= 0.4:
            return "MEDIO - Monitorear y engagement"
        else:
            return "BAJO - Cliente estable"


class NextPurchasePredictionSerializer(serializers.ModelSerializer):
    """Serializer para predicción de próxima compra"""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    predicted_value_formatted = serializers.SerializerMethodField()
    confidence_percentage = serializers.SerializerMethodField()
    days_until_text = serializers.SerializerMethodField()
    
    class Meta:
        model = NextPurchasePrediction
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_predicted_value_formatted(self, obj):
        """Formatear valor predicho en soles"""
        return f"S/ {obj.predicted_value:,.2f}"
    
    def get_confidence_percentage(self, obj):
        """Formatear confidence como porcentaje"""
        return f"{obj.confidence_level:.1f}%"
    
    def get_days_until_text(self, obj):
        """Texto explicativo de días hasta próxima compra"""
        days = obj.days_until_purchase
        
        if days <= 7:
            return f"INMINENTE: {days} días"
        elif days <= 30:
            return f"PRONTO: {days} días"
        elif days <= 90:
            return f"MEDIANO PLAZO: {days} días"
        else:
            return f"LARGO PLAZO: {days} días"


class ProductRecommendationSerializer(serializers.ModelSerializer):
    """Serializer para recomendaciones de productos"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_category = serializers.CharField(source='product.category.name', read_only=True)
    score_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductRecommendation
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_score_percentage(self, obj):
        """Formatear score como porcentaje"""
        return f"{obj.recommendation_score * 100:.1f}%"


class CustomerSegmentationSerializer(serializers.ModelSerializer):
    """Serializer para segmentación de clientes"""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    value_score_text = serializers.SerializerMethodField()
    growth_potential_text = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerSegmentation
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_value_score_text(self, obj):
        """Texto explicativo del value score"""
        score = float(obj.value_score)
        
        if score >= 80:
            return "PREMIUM - Cliente de alto valor"
        elif score >= 60:
            return "ESTÁNDAR - Cliente de valor medio"
        elif score >= 40:
            return "BÁSICO - Cliente de bajo valor"
        else:
            return "NUEVO - Cliente reciente"
    
    def get_growth_potential_text(self, obj):
        """Texto explicativo del potencial de crecimiento"""
        potential = float(obj.growth_potential)
        
        if potential >= 80:
            return "ALTO - Excelente oportunidad"
        elif potential >= 60:
            return "MEDIO - Buena oportunidad"
        elif potential >= 40:
            return "BAJO - Oportunidad limitada"
        else:
            return "MÍNIMO - Poca oportunidad"
