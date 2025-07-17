"""
Modelos financieros y de pronósticos de ingresos
"""

from django.db import models
from decimal import Decimal


class RevenueForecasting(models.Model):
    """Pronósticos de ingresos financieros avanzados"""
    
    FORECAST_TYPES = [
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
    ]
    
    CURRENCY_CHOICES = [
        ('PEN', 'Soles Peruanos'),
        ('USD', 'Dólares Americanos'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='revenue_forecasts'
    )
    forecast_date = models.DateField(verbose_name="Fecha del pronóstico")
    forecast_type = models.CharField(max_length=15, choices=FORECAST_TYPES, verbose_name="Tipo de pronóstico")
    
    # Pronósticos financieros
    predicted_revenue = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Ingresos pronosticados")
    predicted_margin = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Margen pronosticado (%)")
    predicted_cashflow = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Flujo de caja pronosticado")
    
    # Intervalos de confianza
    revenue_lower_bound = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Límite inferior ingresos")
    revenue_upper_bound = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Límite superior ingresos")
    
    # Desglose por categorías
    category_breakdown = models.JSONField(default=dict, verbose_name="Desglose por categorías")
    
    # Factores de influencia
    seasonality_impact = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True, verbose_name="Impacto estacional")
    trend_impact = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True, verbose_name="Impacto de tendencia")
    
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='PEN', verbose_name="Moneda")
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, default=95.00, verbose_name="Nivel de confianza")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pronóstico de ingresos"
        verbose_name_plural = "Pronósticos de ingresos"
        ordering = ['-forecast_date']
        unique_together = [['company', 'forecast_date', 'forecast_type']]
    
    def __str__(self):
        return f"Revenue Forecast {self.forecast_date} - {self.get_forecast_type_display()}"


class FinancialForecastModel(models.Model):
    """Modelo específico para pronósticos financieros"""
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='financial_forecast_models'
    )
    name = models.CharField(max_length=200, verbose_name="Nombre del modelo")
    model_type = models.CharField(max_length=50, verbose_name="Tipo de modelo")
    
    # Configuración específica para finanzas
    forecast_horizon_months = models.PositiveIntegerField(default=12, verbose_name="Horizonte en meses")
    include_seasonality = models.BooleanField(default=True, verbose_name="Incluir estacionalidad")
    include_external_factors = models.BooleanField(default=False, verbose_name="Incluir factores externos")
    
    # Métricas de rendimiento
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Precisión (%)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Modelo de pronóstico financiero"
        verbose_name_plural = "Modelos de pronóstico financiero"
    
    def __str__(self):
        return f"Financial Model {self.name}"


class RevenuePrediction(models.Model):
    """Predicciones específicas de ingresos"""
    
    model = models.ForeignKey(
        FinancialForecastModel,
        on_delete=models.CASCADE,
        related_name='revenue_predictions'
    )
    prediction_date = models.DateField(verbose_name="Fecha de predicción")
    
    # Predicciones
    predicted_revenue = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Ingresos predichos")
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Nivel de confianza")
    
    # Desglose
    category_breakdown = models.JSONField(default=dict, verbose_name="Desglose por categoría")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Predicción de ingresos"
        verbose_name_plural = "Predicciones de ingresos"
        unique_together = [['model', 'prediction_date']]
    
    def __str__(self):
        return f"Revenue Prediction {self.prediction_date} - S/ {self.predicted_revenue}"


class CashFlowForecast(models.Model):
    """Modelo para pronósticos de flujo de caja"""
    
    model = models.ForeignKey(
        FinancialForecastModel, 
        on_delete=models.CASCADE,
        related_name='cash_flow_forecasts'
    )
    forecast_type = models.CharField(max_length=50, choices=[
        ('inflow', 'Entrada'),
        ('outflow', 'Salida'),
        ('net', 'Neto')
    ])
    period_start = models.DateField()
    period_end = models.DateField()
    predicted_amount = models.DecimalField(max_digits=15, decimal_places=2)
    confidence_level = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Pronóstico de flujo de caja"
        verbose_name_plural = "Pronósticos de flujo de caja"


class ProfitabilityAnalysis(models.Model):
    """Modelo para análisis de rentabilidad"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    analysis_type = models.CharField(max_length=50)
    analysis_date = models.DateField()
    profit_margin = models.FloatField()
    revenue = models.DecimalField(max_digits=15, decimal_places=2)
    costs = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Análisis de rentabilidad"
        verbose_name_plural = "Análisis de rentabilidad"


class FinancialRiskAssessment(models.Model):
    """Modelo para evaluación de riesgos financieros"""
    
    company = models.ForeignKey('authentication.Company', on_delete=models.CASCADE)
    risk_type = models.CharField(max_length=50)
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('critical', 'Crítico')
    ])
    assessment_date = models.DateField()
    probability = models.FloatField()
    impact_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Evaluación de riesgo financiero"
        verbose_name_plural = "Evaluaciones de riesgo financiero"


class SeasonalityAnalysis(models.Model):
    """Modelo para análisis de estacionalidad"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    season_type = models.CharField(max_length=50)
    analysis_date = models.DateField()
    seasonal_factor = models.FloatField()
    peak_period = models.CharField(max_length=100)
    low_period = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Análisis de estacionalidad"
        verbose_name_plural = "Análisis de estacionalidad"


class CostOptimizationModel(models.Model):
    """Modelo para optimización de costos"""
    
    company = models.ForeignKey('authentication.Company', on_delete=models.CASCADE)
    optimization_type = models.CharField(max_length=50)
    current_cost = models.DecimalField(max_digits=15, decimal_places=2)
    optimized_cost = models.DecimalField(max_digits=15, decimal_places=2)
    savings_potential = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Modelo de optimización de costos"
        verbose_name_plural = "Modelos de optimización de costos"


class RevenueBreakdown(models.Model):
    """Modelo para desglose de ingresos"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    breakdown_type = models.CharField(max_length=50)
    period_start = models.DateField()
    period_end = models.DateField()
    revenue_amount = models.DecimalField(max_digits=15, decimal_places=2)
    percentage_of_total = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Desglose de ingresos"
        verbose_name_plural = "Desgloses de ingresos"


class FinancialScenario(models.Model):
    """Modelo para escenarios financieros"""
    
    company = models.ForeignKey('authentication.Company', on_delete=models.CASCADE)
    scenario_type = models.CharField(max_length=50)
    scenario_name = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    probability = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Escenario financiero"
        verbose_name_plural = "Escenarios financieros"


class ProfitMarginAnalysis(models.Model):
    """Modelo para análisis de margen de beneficio"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    margin_type = models.CharField(max_length=50)
    analysis_date = models.DateField()
    gross_margin = models.FloatField()
    net_margin = models.FloatField()
    trend_direction = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Análisis de margen de beneficio"
        verbose_name_plural = "Análisis de márgenes de beneficio"


class FinancialTrendAnalysis(models.Model):
    """Modelo para análisis de tendencias financieras"""
    
    company = models.ForeignKey('authentication.Company', on_delete=models.CASCADE)
    trend_type = models.CharField(max_length=50)
    analysis_date = models.DateField()
    trend_strength = models.FloatField()
    trend_direction = models.CharField(max_length=20)
    forecast_reliability = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Análisis de tendencia financiera"
        verbose_name_plural = "Análisis de tendencias financieras"
