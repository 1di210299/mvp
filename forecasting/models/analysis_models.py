"""
Modelos de análisis avanzado y ROI
"""

from django.db import models


class SupplierROIAnalysis(models.Model):
    """Análisis de ROI por proveedor"""
    
    supplier = models.OneToOneField(
        'inventory.Supplier',
        on_delete=models.CASCADE,
        related_name='roi_analysis'
    )
    
    # Métricas financieras
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Costo total")
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Ingresos totales")
    gross_profit = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Ganancia bruta")
    roi_percentage = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="ROI (%)")
    
    # Métricas operativas
    avg_delivery_time = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Tiempo promedio entrega")
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Puntuación de calidad")
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Tasa entrega a tiempo")
    
    # Análisis de costos
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Costo por unidad")
    cost_trend = models.CharField(max_length=15, choices=[
        ('decreasing', 'Disminuyendo'),
        ('stable', 'Estable'),
        ('increasing', 'Aumentando'),
    ], verbose_name="Tendencia de costos")
    
    # Recomendaciones
    performance_rating = models.CharField(max_length=15, choices=[
        ('excellent', 'Excelente'),
        ('good', 'Bueno'),
        ('average', 'Promedio'),
        ('poor', 'Malo'),
    ], verbose_name="Calificación de rendimiento")
    
    recommendations = models.JSONField(default=list, verbose_name="Recomendaciones")
    
    # Período de análisis
    analysis_start_date = models.DateField(verbose_name="Fecha inicio análisis")
    analysis_end_date = models.DateField(verbose_name="Fecha fin análisis")
    
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Análisis ROI de proveedor"
        verbose_name_plural = "Análisis ROI de proveedores"
        ordering = ['-roi_percentage']
    
    def __str__(self):
        return f"ROI {self.supplier.name} - {self.roi_percentage:.2f}%"


class PriceElasticityAnalysis(models.Model):
    """Análisis detallado de elasticidad de precios"""
    
    product = models.OneToOneField(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='elasticity_analysis'
    )
    
    # Elasticidad calculada
    elasticity_coefficient = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Coeficiente")
    r_squared = models.DecimalField(max_digits=5, decimal_places=4, verbose_name="R²")
    
    # Recomendaciones de precio
    optimal_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio óptimo")
    price_sensitivity = models.CharField(max_length=20, choices=[
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ], verbose_name="Sensibilidad")
    
    # Datos utilizados
    data_points = models.PositiveIntegerField(verbose_name="Puntos de datos")
    analysis_period_days = models.PositiveIntegerField(verbose_name="Período de análisis")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Análisis de elasticidad de precio"
        verbose_name_plural = "Análisis de elasticidad de precios"
    
    def __str__(self):
        return f"Price Elasticity {self.product.name} - {self.elasticity_coefficient}"


class TrendingProductPrediction(models.Model):
    """Predicciones de productos en tendencia"""
    
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='trending_predictions'
    )
    prediction_date = models.DateField(verbose_name="Fecha de predicción")
    
    # Métricas de tendencia
    trend_score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Score de tendencia")
    growth_rate = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Tasa de crecimiento")
    confidence = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Confianza")
    
    # Factores contribuyentes
    factors = models.JSONField(default=list, verbose_name="Factores")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Predicción de producto en tendencia"
        verbose_name_plural = "Predicciones de productos en tendencia"
        unique_together = [['product', 'prediction_date']]
    
    def __str__(self):
        return f"Trending {self.product.name} - {self.trend_score}"


class StockoutPrediction(models.Model):
    """Predicciones de agotamiento de stock"""
    
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='stockout_predictions'
    )
    prediction_date = models.DateField(verbose_name="Fecha de predicción")
    
    # Predicción de agotamiento
    predicted_stockout_date = models.DateField(null=True, blank=True, verbose_name="Fecha predicha de agotamiento")
    stockout_probability = models.DecimalField(max_digits=5, decimal_places=4, verbose_name="Probabilidad de agotamiento")
    days_until_stockout = models.PositiveIntegerField(null=True, blank=True, verbose_name="Días hasta agotamiento")
    
    # Factores de riesgo
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Stock actual")
    predicted_demand = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Demanda predicha")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Predicción de agotamiento"
        verbose_name_plural = "Predicciones de agotamiento"
        unique_together = [['product', 'prediction_date']]
    
    def __str__(self):
        return f"Stockout {self.product.name} - {self.stockout_probability:.2%}"
