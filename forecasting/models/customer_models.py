"""
Modelos de customer intelligence y análisis de clientes
"""

from django.db import models


class CustomerLifetimeValue(models.Model):
    """Análisis de valor de vida del cliente (CLV)"""
    
    customer = models.OneToOneField(
        'inventory.Customer',
        on_delete=models.CASCADE,
        related_name='lifetime_value'
    )
    
    # Métricas CLV
    predicted_clv = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="CLV Predicho")
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, verbose_name="Valor actual")
    predicted_lifetime_months = models.PositiveIntegerField(default=0, verbose_name="Vida predicha (meses)")
    
    # Campos adicionales requeridos por ML service
    clv_confidence = models.DecimalField(max_digits=6, decimal_places=4, default=0.0, verbose_name="Confianza CLV")
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="Valor promedio orden")
    customer_lifespan_months = models.PositiveIntegerField(default=0, verbose_name="Duración de vida (meses)")
    recency_days = models.PositiveIntegerField(default=0, verbose_name="Días desde última compra")
    
    # Análisis RFM
    frequency_score = models.PositiveIntegerField(default=1, verbose_name="Puntaje frecuencia (1-5)")
    monetary_score = models.PositiveIntegerField(default=1, verbose_name="Puntaje monetario (1-5)")
    rfm_segment = models.CharField(max_length=20, default='unknown', verbose_name="Segmento RFM")
    
    # Probabilidades
    churn_probability = models.DecimalField(max_digits=5, decimal_places=4, default=0.0, verbose_name="Probabilidad de abandono")
    next_purchase_probability = models.DecimalField(max_digits=5, decimal_places=4, default=0.0, verbose_name="Probabilidad próxima compra")
    
    # Patrones de compra
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="Valor promedio de orden")
    purchase_frequency = models.DecimalField(max_digits=8, decimal_places=4, default=0.0, verbose_name="Frecuencia de compra")
    last_purchase_date = models.DateField(null=True, blank=True, verbose_name="Última compra")
    
    # Segmentación
    customer_segment = models.CharField(max_length=20, choices=[
        ('champion', 'Campeón'),
        ('loyal', 'Leal'),
        ('potential', 'Potencial'),
        ('new', 'Nuevo'),
        ('at_risk', 'En riesgo'),
        ('lost', 'Perdido'),
    ], verbose_name="Segmento de cliente")
    
    # Recomendaciones
    next_best_products = models.JSONField(default=list, verbose_name="Próximos mejores productos")
    
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Valor de vida del cliente"
        verbose_name_plural = "Valores de vida de clientes"
        ordering = ['-predicted_clv']
    
    def __str__(self):
        return f"CLV {self.customer.name} - {self.predicted_clv}"


class ChurnPrediction(models.Model):
    """Predicción de abandono de clientes"""
    
    RISK_LEVELS = [
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('critical', 'Crítico'),
    ]
    
    RETENTION_STRATEGIES = [
        ('discount', 'Descuento'),
        ('loyalty_program', 'Programa de lealtad'),
        ('personal_attention', 'Atención personalizada'),
        ('product_recommendation', 'Recomendación de productos'),
        ('contact_campaign', 'Campaña de contacto'),
    ]
    
    customer = models.OneToOneField(
        'inventory.Customer',
        on_delete=models.CASCADE,
        related_name='churn_prediction'
    )
    
    # Predicción de churn
    churn_probability = models.DecimalField(max_digits=5, decimal_places=4, default=0.0, verbose_name="Probabilidad de abandono")
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='low', verbose_name="Nivel de riesgo")
    
    # Campos adicionales requeridos por ML service
    churn_risk_level = models.CharField(max_length=20, default='unknown', verbose_name="Nivel de riesgo churn")
    declining_order_value = models.BooleanField(default=False, verbose_name="Valor de orden en declive")
    declining_purchase_frequency = models.BooleanField(default=False, verbose_name="Frecuencia en declive")
    engagement_score = models.DecimalField(max_digits=6, decimal_places=4, default=0.0, verbose_name="Puntaje engagement")
    loyalty_score = models.DecimalField(max_digits=6, decimal_places=4, default=0.0, verbose_name="Puntaje lealtad")
    negative_trend_months = models.PositiveIntegerField(default=0, verbose_name="Meses tendencia negativa")
    recommended_action_priority = models.CharField(max_length=20, default='low', verbose_name="Prioridad acción")
    
    # Factores de riesgo
    days_since_last_purchase = models.PositiveIntegerField(default=0, verbose_name="Días desde última compra")
    purchase_frequency_decline = models.DecimalField(max_digits=6, decimal_places=4, default=0.0, verbose_name="Declive en frecuencia")
    value_decline = models.DecimalField(max_digits=6, decimal_places=4, default=0.0, verbose_name="Declive en valor")
    
    # Factores de influencia
    risk_factors = models.JSONField(default=list, verbose_name="Factores de riesgo")
    
    # Estrategia de retención recomendada
    retention_strategy = models.CharField(
        max_length=30,
        choices=RETENTION_STRATEGIES,
        verbose_name="Estrategia de retención"
    )
    retention_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Presupuesto de retención")
    
    # Resultados de la estrategia
    strategy_applied = models.BooleanField(default=False, verbose_name="Estrategia aplicada")
    strategy_effective = models.BooleanField(null=True, blank=True, verbose_name="Estrategia efectiva")
    
    predicted_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Predicción de abandono"
        verbose_name_plural = "Predicciones de abandono"
        ordering = ['-churn_probability']
    
    def __str__(self):
        return f"Churn {self.customer.name} - {self.churn_probability:.2%}"


class MarketBasketAnalysis(models.Model):
    """Análisis de canasta de mercado - productos que se venden juntos"""
    
    RECOMMENDATION_STRENGTH = [
        ('weak', 'Débil'),
        ('moderate', 'Moderada'),
        ('strong', 'Fuerte'),
        ('very_strong', 'Muy fuerte'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='market_basket_analyses'
    )
    
    # Productos analizados
    product_a = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='basket_analyses_as_a'
    )
    product_b = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='basket_analyses_as_b'
    )
    
    # Métricas de asociación
    support = models.DecimalField(max_digits=6, decimal_places=4, verbose_name="Soporte")  # P(A,B)
    confidence = models.DecimalField(max_digits=6, decimal_places=4, verbose_name="Confianza")  # P(B|A)
    lift = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Elevación")  # Confidence/P(B)
    
    # Estadísticas
    transactions_with_both = models.PositiveIntegerField(verbose_name="Transacciones con ambos")
    transactions_with_a = models.PositiveIntegerField(verbose_name="Transacciones con A")
    total_transactions = models.PositiveIntegerField(verbose_name="Total transacciones")
    
    # Recomendación
    recommendation_strength = models.CharField(
        max_length=15,
        choices=RECOMMENDATION_STRENGTH,
        verbose_name="Fuerza de recomendación"
    )
    
    # Período de análisis
    analysis_start_date = models.DateField(verbose_name="Fecha inicio análisis")
    analysis_end_date = models.DateField(verbose_name="Fecha fin análisis")
    
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Análisis de canasta de mercado"
        verbose_name_plural = "Análisis de canasta de mercado"
        ordering = ['-lift']
        unique_together = [['product_a', 'product_b', 'analysis_start_date']]
    
    def __str__(self):
        return f"Basket {self.product_a.name} + {self.product_b.name} (Lift: {self.lift})"


class ProductRecommendation(models.Model):
    """Recomendaciones de productos para clientes"""
    
    RECOMMENDATION_TYPES = [
        ('cross_sell', 'Venta cruzada'),
        ('up_sell', 'Venta adicional'),
        ('repeat_purchase', 'Compra repetida'),
        ('seasonal', 'Estacional'),
        ('trending', 'Tendencia'),
    ]
    
    customer = models.ForeignKey(
        'inventory.Customer',
        on_delete=models.CASCADE,
        related_name='product_recommendations'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='customer_recommendations'
    )
    
    # Relación opcional con predicción de próxima compra
    next_purchase = models.ForeignKey(
        'NextPurchasePrediction',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='product_recommendations'
    )
    
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES, verbose_name="Tipo de recomendación")
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, verbose_name="Puntuación de confianza")
    
    # Factores de la recomendación
    purchase_probability = models.DecimalField(max_digits=5, decimal_places=4, verbose_name="Probabilidad de compra")
    expected_quantity = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Cantidad esperada")
    expected_revenue = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ingresos esperados")
    
    # Base de la recomendación
    reasoning = models.TextField(verbose_name="Razonamiento")
    similar_customers = models.JSONField(default=list, verbose_name="Clientes similares")
    
    # Tiempo óptimo
    best_contact_time = models.DateTimeField(null=True, blank=True, verbose_name="Mejor momento de contacto")
    expires_at = models.DateTimeField(verbose_name="Expira el")
    
    # Seguimiento
    presented_to_customer = models.BooleanField(default=False, verbose_name="Presentado al cliente")
    customer_response = models.CharField(max_length=20, choices=[
        ('accepted', 'Aceptado'),
        ('declined', 'Rechazado'),
        ('ignored', 'Ignorado'),
        ('pending', 'Pendiente'),
    ], default='pending', verbose_name="Respuesta del cliente")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Recomendación de producto"
        verbose_name_plural = "Recomendaciones de productos"
        ordering = ['-confidence_score']
        unique_together = [['customer', 'product', 'recommendation_type']]
    
    def __str__(self):
        return f"Recommendation {self.customer.name} - {self.product.name}"


class NextPurchasePrediction(models.Model):
    """Predicciones de próxima compra de clientes"""
    
    customer = models.ForeignKey(
        'inventory.Customer',
        on_delete=models.CASCADE,
        related_name='next_purchase_predictions'
    )
    
    # Predicción temporal
    predicted_date = models.DateField(verbose_name="Fecha predicha")
    days_until_purchase = models.PositiveIntegerField(verbose_name="Días hasta compra")
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Nivel de confianza")
    
    # Predicción de valor
    predicted_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor predicho")
    predicted_quantity = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Cantidad predicha")
    
    # Productos recomendados
    recommended_products = models.ManyToManyField(
        'inventory.Product',
        blank=True,
        verbose_name="Productos recomendados"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Predicción de próxima compra"
        verbose_name_plural = "Predicciones de próximas compras"
    
    def __str__(self):
        return f"Next Purchase {self.customer.name} - {self.predicted_date}"


class CustomerSegmentation(models.Model):
    """Segmentación automática de clientes"""
    
    customer = models.OneToOneField(
        'inventory.Customer',
        on_delete=models.CASCADE,
        related_name='segmentation'
    )
    
    # Segmento principal
    primary_segment = models.CharField(max_length=20, choices=[
        ('vip', 'VIP'),
        ('frequent', 'Frecuente'),
        ('occasional', 'Ocasional'),
        ('new', 'Nuevo'),
        ('dormant', 'Dormante'),
        ('lost', 'Perdido'),
    ], verbose_name="Segmento principal")
    
    # Scores
    value_score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Score de valor")
    frequency_score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Score de frecuencia")
    recency_score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Score de recencia")
    
    # Atributos del segmento
    segment_attributes = models.JSONField(default=dict, verbose_name="Atributos del segmento")
    
    # Recomendaciones
    marketing_strategy = models.CharField(max_length=50, verbose_name="Estrategia de marketing")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Segmentación de cliente"
        verbose_name_plural = "Segmentaciones de clientes"
    
    def __str__(self):
        return f"Segmentation {self.customer.name} - {self.primary_segment}"


# ===== MODELOS ADICIONALES DE CUSTOMER INTELLIGENCE =====

class CustomerBehaviorPattern(models.Model):
    """Modelo para patrones de comportamiento de clientes"""
    
    customer = models.ForeignKey('inventory.Customer', on_delete=models.CASCADE)
    pattern_type = models.CharField(max_length=50)
    behavior_category = models.CharField(max_length=50)
    pattern_strength = models.FloatField()
    frequency = models.CharField(max_length=50)
    analysis_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Patrón de comportamiento de cliente"
        verbose_name_plural = "Patrones de comportamiento de clientes"


class PriceOptimization(models.Model):
    """Modelo para optimización de precios"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    optimization_type = models.CharField(max_length=50)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    recommended_price = models.DecimalField(max_digits=10, decimal_places=2)
    expected_demand_change = models.FloatField()
    revenue_impact = models.DecimalField(max_digits=15, decimal_places=2)
    analysis_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Optimización de precio"
        verbose_name_plural = "Optimizaciones de precio"


class CrossSellModel(models.Model):
    """Modelo para cross-selling"""
    
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='crosssell_primary')
    recommended_product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='crosssell_recommended')
    recommendation_score = models.FloatField()
    confidence_level = models.FloatField()
    historical_data_support = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Modelo de cross-sell"
        verbose_name_plural = "Modelos de cross-sell"


class CustomerSatisfactionModel(models.Model):
    """Modelo para satisfacción del cliente"""
    
    customer = models.ForeignKey('inventory.Customer', on_delete=models.CASCADE)
    satisfaction_score = models.FloatField()
    feedback_sentiment = models.CharField(max_length=20)
    key_factors = models.JSONField(default=dict)
    improvement_suggestions = models.TextField()
    analysis_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Modelo de satisfacción del cliente"
        verbose_name_plural = "Modelos de satisfacción del cliente"


class LoyaltyProgramModel(models.Model):
    """Modelo para programa de lealtad"""
    
    customer = models.ForeignKey('inventory.Customer', on_delete=models.CASCADE)
    loyalty_score = models.FloatField()
    loyalty_tier = models.CharField(max_length=50)
    points_balance = models.IntegerField()
    engagement_level = models.CharField(max_length=20)
    next_reward_threshold = models.IntegerField()
    analysis_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Modelo de programa de lealtad"
        verbose_name_plural = "Modelos de programa de lealtad"


class CustomerEngagementModel(models.Model):
    """Modelo para engagement de clientes"""
    
    customer = models.ForeignKey('inventory.Customer', on_delete=models.CASCADE)
    engagement_score = models.FloatField()
    engagement_level = models.CharField(max_length=20)
    interaction_frequency = models.FloatField()
    preferred_channels = models.JSONField(default=list)
    last_interaction = models.DateTimeField()
    analysis_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Modelo de engagement de cliente"
        verbose_name_plural = "Modelos de engagement de cliente"
