"""
Modelos de demanda, inventario y optimización de stock
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class DemandPatternAnalysis(models.Model):
    """Análisis de patrones de demanda"""
    
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='demand_patterns'
    )
    
    # Patrones detectados
    has_weekly_pattern = models.BooleanField(default=False, verbose_name="Patrón semanal")
    has_monthly_pattern = models.BooleanField(default=False, verbose_name="Patrón mensual")
    has_seasonal_pattern = models.BooleanField(default=False, verbose_name="Patrón estacional")
    
    # Fuerza de los patrones
    weekly_strength = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Fuerza semanal")
    monthly_strength = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Fuerza mensual")
    seasonal_strength = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Fuerza estacional")
    
    # Datos del patrón
    pattern_data = models.JSONField(default=dict, verbose_name="Datos del patrón")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Análisis de patrón de demanda"
        verbose_name_plural = "Análisis de patrones de demanda"
    
    def __str__(self):
        return f"Demand Pattern {self.product.name}"


class PriceElasticity(models.Model):
    """Análisis de elasticidad de precios"""
    
    product = models.OneToOneField(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='price_elasticity'
    )
    
    # Elasticidad
    elasticity_coefficient = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Coeficiente de elasticidad")
    demand_sensitivity = models.CharField(max_length=15, choices=[
        ('inelastic', 'Inelástica'),
        ('unit_elastic', 'Unitaria'),
        ('elastic', 'Elástica'),
        ('highly_elastic', 'Muy elástica'),
    ], verbose_name="Sensibilidad de demanda")
    
    # Precios óptimos
    optimal_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio óptimo")
    current_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio actual")
    recommended_price_change = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Cambio recomendado (%)")
    
    # Impacto estimado
    estimated_demand_change = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Cambio estimado en demanda")
    estimated_revenue_impact = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Impacto estimado en ingresos")
    
    # Período de análisis
    analysis_period_days = models.PositiveIntegerField(verbose_name="Período de análisis (días)")
    price_points_analyzed = models.PositiveIntegerField(verbose_name="Puntos de precio analizados")
    
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Elasticidad de precio"
        verbose_name_plural = "Elasticidades de precio"
        ordering = ['-estimated_revenue_impact']
    
    def __str__(self):
        return f"Price Elasticity {self.product.name} - {self.elasticity_coefficient}"


class SeasonalityPattern(models.Model):
    """Patrones estacionales automáticos"""
    
    PATTERN_TYPES = [
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
        ('holiday', 'Festividades'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='seasonality_patterns'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='seasonality_patterns'
    )
    
    pattern_type = models.CharField(max_length=15, choices=PATTERN_TYPES, verbose_name="Tipo de patrón")
    
    # Patrón detectado
    pattern_strength = models.DecimalField(max_digits=6, decimal_places=4, verbose_name="Fuerza del patrón")
    peak_periods = models.JSONField(default=list, verbose_name="Períodos pico")  # ["December", "June"]
    low_periods = models.JSONField(default=list, verbose_name="Períodos bajos")
    
    # Multiplicadores estacionales
    seasonal_multipliers = models.JSONField(default=dict, verbose_name="Multiplicadores estacionales")
    
    # Estadísticas
    data_points_analyzed = models.PositiveIntegerField(verbose_name="Puntos de datos analizados")
    pattern_confidence = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Confianza del patrón")
    
    # Próximas predicciones
    next_peak_date = models.DateField(null=True, blank=True, verbose_name="Próxima fecha pico")
    next_low_date = models.DateField(null=True, blank=True, verbose_name="Próxima fecha baja")
    
    detected_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Patrón estacional"
        verbose_name_plural = "Patrones estacionales"
        ordering = ['-pattern_strength']
        unique_together = [['product', 'pattern_type']]
    
    def __str__(self):
        return f"Seasonality {self.product.name} - {self.get_pattern_type_display()}"


class OptimalStockLevel(models.Model):
    """Niveles de stock óptimos calculados matemáticamente"""
    
    product = models.OneToOneField(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='optimal_stock_level'
    )
    location = models.ForeignKey(
        'inventory.Location',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='optimal_stock_levels'
    )
    
    # Niveles óptimos
    optimal_stock = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Stock óptimo")
    safety_stock = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Stock de seguridad")
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Punto de reorden")
    economic_order_quantity = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Cantidad económica de pedido")
    
    # Parámetros del cálculo
    holding_cost_rate = models.DecimalField(max_digits=6, decimal_places=4, verbose_name="Tasa de costo de mantenimiento")
    ordering_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo de pedido")
    stockout_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo de quiebre")
    
    # Demanda estadística
    avg_daily_demand = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Demanda diaria promedio")
    demand_variability = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Variabilidad de demanda")
    lead_time_variability = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Variabilidad tiempo entrega")
    
    # Resultados esperados
    expected_stockout_frequency = models.DecimalField(max_digits=6, decimal_places=4, verbose_name="Frecuencia esperada de quiebre")
    expected_annual_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Costo anual esperado")
    service_level = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Nivel de servicio (%)")
    
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Nivel de stock óptimo"
        verbose_name_plural = "Niveles de stock óptimos"
        ordering = ['-expected_annual_cost']
        unique_together = [['product', 'location']]
    
    def __str__(self):
        return f"Optimal Stock {self.product.name} - {self.optimal_stock}"


# ===== MODELOS ADICIONALES DE DEMANDA E INVENTARIO =====

class DemandPattern(models.Model):
    """Modelo para patrones de demanda"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    pattern_type = models.CharField(max_length=50)
    pattern_date = models.DateField()
    pattern_strength = models.FloatField()
    frequency = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Patrón de demanda"
        verbose_name_plural = "Patrones de demanda"


class AdvancedDemandForecast(models.Model):
    """Modelo para pronósticos avanzados de demanda"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    model = models.ForeignKey('ForecastModel', on_delete=models.CASCADE)
    forecast_type = models.CharField(max_length=50)
    forecast_date = models.DateField()
    predicted_demand = models.FloatField()
    confidence_interval = models.JSONField()
    external_factors = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Pronóstico avanzado de demanda"
        verbose_name_plural = "Pronósticos avanzados de demanda"


class SeasonalPattern(models.Model):
    """Modelo para patrones estacionales"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    season_type = models.CharField(max_length=50)
    seasonal_factor = models.FloatField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Patrón estacional"
        verbose_name_plural = "Patrones estacionales"


class InventoryOptimizationModel(models.Model):
    """Modelo para optimización de inventario"""
    
    company = models.ForeignKey('authentication.Company', on_delete=models.CASCADE)
    model_type = models.CharField(max_length=50)
    optimization_algorithm = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    parameters = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Modelo de optimización de inventario"
        verbose_name_plural = "Modelos de optimización de inventario"


class StockLevelRecommendation(models.Model):
    """Modelo para recomendaciones de nivel de stock"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    model = models.ForeignKey('InventoryOptimizationModel', on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=50)
    recommended_stock = models.FloatField()
    current_stock = models.FloatField()
    safety_stock = models.FloatField()
    priority = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Recomendación de nivel de stock"
        verbose_name_plural = "Recomendaciones de nivel de stock"


class SupplierPerformanceModel(models.Model):
    """Modelo para rendimiento de proveedores"""
    
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.CASCADE)
    analysis_date = models.DateField()
    performance_score = models.FloatField()
    delivery_reliability = models.FloatField()
    quality_score = models.FloatField()
    cost_effectiveness = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Modelo de rendimiento de proveedor"
        verbose_name_plural = "Modelos de rendimiento de proveedores"


class ProcurementOptimization(models.Model):
    """Modelo para optimización de procuramiento"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.CASCADE)
    optimization_type = models.CharField(max_length=50)
    recommended_quantity = models.FloatField()
    recommended_timing = models.DateField()
    cost_savings = models.DecimalField(max_digits=15, decimal_places=2)
    analysis_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Optimización de procuramiento"
        verbose_name_plural = "Optimizaciones de procuramiento"


class SupplierRiskAnalysis(models.Model):
    """Modelo para análisis de riesgo de proveedores"""
    
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.CASCADE)
    risk_type = models.CharField(max_length=50)
    risk_level = models.CharField(max_length=20)
    probability = models.FloatField()
    impact_score = models.FloatField()
    mitigation_strategy = models.TextField()
    analysis_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Análisis de riesgo de proveedor"
        verbose_name_plural = "Análisis de riesgo de proveedores"


class InventoryTurnoverAnalysis(models.Model):
    """Modelo para análisis de rotación de inventario"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    period_type = models.CharField(max_length=20)
    turnover_ratio = models.FloatField()
    days_in_inventory = models.IntegerField()
    performance_category = models.CharField(max_length=50)
    analysis_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Análisis de rotación de inventario"
        verbose_name_plural = "Análisis de rotación de inventario"
