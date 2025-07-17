"""
Serializers para análisis e insights
"""

from rest_framework import serializers
from ..models import (
    SupplierROIAnalysis, MarketBasketAnalysis, PriceElasticityAnalysis
)


class SupplierROIAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis ROI de proveedores"""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    roi_percentage = serializers.SerializerMethodField()
    profit_margin_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierROIAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_roi_percentage(self, obj):
        """Formatear ROI como porcentaje"""
        return f"{obj.roi_score:.2f}%"
    
    def get_profit_margin_percentage(self, obj):
        """Formatear profit margin como porcentaje"""
        return f"{obj.profit_margin:.2f}%"


class MarketBasketAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis de market basket"""
    
    product_a_name = serializers.CharField(source='product_a.name', read_only=True)
    product_b_name = serializers.CharField(source='product_b.name', read_only=True)
    support_percentage = serializers.SerializerMethodField()
    confidence_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = MarketBasketAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_support_percentage(self, obj):
        """Formatear support como porcentaje"""
        return f"{obj.support * 100:.2f}%"
    
    def get_confidence_percentage(self, obj):
        """Formatear confidence como porcentaje"""
        return f"{obj.confidence * 100:.2f}%"


class PriceElasticityAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis de elasticidad de precios"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    elasticity_interpretation = serializers.SerializerMethodField()
    
    class Meta:
        model = PriceElasticityAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_elasticity_interpretation(self, obj):
        """Interpretar coeficiente de elasticidad"""
        elasticity = float(obj.elasticity_coefficient)
        
        if elasticity > 1:
            return "Elástico - Muy sensible al precio"
        elif elasticity > 0.5:
            return "Moderadamente elástico"
        elif elasticity > 0:
            return "Inelástico - Poco sensible al precio"
        else:
            return "Bien Giffen - Aumenta demanda con precio"
