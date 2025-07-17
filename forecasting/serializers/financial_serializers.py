"""
Serializers para modelos financieros
"""

from rest_framework import serializers
from ..models import (
    FinancialForecastModel, RevenuePrediction, CashFlowForecast,
    ProfitabilityAnalysis, FinancialRiskAssessment, SeasonalityAnalysis,
    CostOptimizationModel, RevenueBreakdown, FinancialScenario,
    ProfitMarginAnalysis, FinancialTrendAnalysis
)


class FinancialForecastModelSerializer(serializers.ModelSerializer):
    """Serializer para modelo de pronóstico financiero"""
    
    class Meta:
        model = FinancialForecastModel
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class RevenuePredictionSerializer(serializers.ModelSerializer):
    """Serializer para predicción de ingresos"""
    
    predicted_revenue_formatted = serializers.SerializerMethodField()
    confidence_level_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = RevenuePrediction
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_predicted_revenue_formatted(self, obj):
        """Formatear revenue en soles"""
        return f"S/ {obj.predicted_revenue:,.2f}"
    
    def get_confidence_level_percentage(self, obj):
        """Formatear confidence level como porcentaje"""
        return f"{obj.confidence_level:.1f}%"


class CashFlowForecastSerializer(serializers.ModelSerializer):
    """Serializer para pronósticos de flujo de caja"""
    
    predicted_amount_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = CashFlowForecast
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_predicted_amount_formatted(self, obj):
        return f"S/ {obj.predicted_amount:,.2f}"


class ProfitabilityAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis de rentabilidad"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    revenue_formatted = serializers.SerializerMethodField()
    costs_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ProfitabilityAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_revenue_formatted(self, obj):
        return f"S/ {obj.revenue:,.2f}"
    
    def get_costs_formatted(self, obj):
        return f"S/ {obj.costs:,.2f}"


class FinancialRiskAssessmentSerializer(serializers.ModelSerializer):
    """Serializer para evaluación de riesgos financieros"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = FinancialRiskAssessment
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class SeasonalityAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis de estacionalidad"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SeasonalityAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class CostOptimizationModelSerializer(serializers.ModelSerializer):
    """Serializer para modelos de optimización de costos"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    savings_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = CostOptimizationModel
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_savings_formatted(self, obj):
        return f"S/ {obj.savings_potential:,.2f}"


class RevenueBreakdownSerializer(serializers.ModelSerializer):
    """Serializer para desglose de ingresos"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    revenue_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = RevenueBreakdown
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_revenue_formatted(self, obj):
        return f"S/ {obj.revenue_amount:,.2f}"


class FinancialScenarioSerializer(serializers.ModelSerializer):
    """Serializer para escenarios financieros"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = FinancialScenario
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class ProfitMarginAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis de margen de beneficio"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProfitMarginAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class FinancialTrendAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis de tendencias financieras"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = FinancialTrendAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
