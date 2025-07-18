"""
AI MODELS - Arquitectura Híbrida ML + AI
========================================

Modelos para integración ML tradicional con AI insights:
- Tracking de API usage y costos de AI
- Versionado de prompts AI
- Schema AI insights (sentiment, strategy recommendations)
- Sistema híbrido ML-AI unificado

Autor: Sistema ML Forecasting
Fecha: 2025-07-17
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from decimal import Decimal
import uuid


class AIPromptVersion(models.Model):
    """
    Sistema de versionado para prompts AI
    Permite tracking de evolución de prompts y A/B testing
    """
    
    PROMPT_TYPES = [
        ('sentiment_analysis', 'Análisis de Sentimiento'),
        ('strategy_recommendation', 'Recomendación de Estrategia'),
        ('customer_insight', 'Insight de Cliente'),
        ('demand_prediction', 'Predicción de Demanda'),
        ('product_recommendation', 'Recomendación de Producto'),
        ('market_analysis', 'Análisis de Mercado'),
        ('risk_assessment', 'Evaluación de Riesgo'),
        ('optimization', 'Optimización'),
        ('custom', 'Personalizado'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('testing', 'En Pruebas'),
        ('active', 'Activo'),
        ('deprecated', 'Depreciado'),
        ('archived', 'Archivado'),
    ]
    
    # Identificación única
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Información del prompt
    name = models.CharField(max_length=200, verbose_name="Nombre del prompt")
    description = models.TextField(blank=True, verbose_name="Descripción")
    prompt_type = models.CharField(max_length=30, choices=PROMPT_TYPES)
    
    # Versionado
    version = models.CharField(max_length=20, verbose_name="Versión (ej: 1.0.0)")
    parent_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_versions'
    )
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=False)
    
    # Contenido del prompt
    system_prompt = models.TextField(verbose_name="System prompt")
    user_prompt_template = models.TextField(verbose_name="Template del user prompt")
    assistant_prompt = models.TextField(blank=True, verbose_name="Assistant prompt")
    
    # Configuración del modelo AI
    ai_model = models.CharField(max_length=100, default='gpt-4', verbose_name="Modelo AI")
    temperature = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('0.7'),
        validators=[MinValueValidator(0), MaxValueValidator(2)]
    )
    max_tokens = models.PositiveIntegerField(default=1000)
    top_p = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('1.0'),
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    # Métricas de performance
    avg_response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    avg_tokens_used = models.PositiveIntegerField(null=True, blank=True)
    
    # A/B Testing
    test_group = models.CharField(max_length=50, blank=True, verbose_name="Grupo de prueba")
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Audit trail
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ai_prompts'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['name', 'version']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prompt_type', 'status']),
            models.Index(fields=['is_active', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_prompt_type_display()})"


class AIAPIUsage(models.Model):
    """
    Tracking detallado de uso de API AI y costos
    Para monitoreo de presupuesto y optimización
    """
    
    API_PROVIDERS = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google AI'),
        ('azure', 'Azure OpenAI'),
        ('aws', 'AWS Bedrock'),
        ('custom', 'API Personalizada'),
    ]
    
    REQUEST_TYPES = [
        ('completion', 'Text Completion'),
        ('chat', 'Chat Completion'),
        ('embedding', 'Embeddings'),
        ('fine_tuning', 'Fine-tuning'),
        ('image_generation', 'Generación de Imagen'),
        ('image_analysis', 'Análisis de Imagen'),
        ('speech_to_text', 'Speech to Text'),
        ('text_to_speech', 'Text to Speech'),
    ]
    
    # Identificación de la empresa
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='ai_api_usage'
    )
    
    # Información del request
    prompt_version = models.ForeignKey(
        AIPromptVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_usage'
    )
    
    # Proveedor y configuración
    api_provider = models.CharField(max_length=20, choices=API_PROVIDERS)
    model_name = models.CharField(max_length=100, verbose_name="Nombre del modelo")
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    
    # Métricas del request
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    
    # Costos (en USD)
    input_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    output_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Performance
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    status_code = models.PositiveIntegerField(default=200)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Contexto de uso
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ai_api_requests'
    )
    session_id = models.CharField(max_length=100, blank=True)
    request_context = models.JSONField(default=dict, verbose_name="Contexto del request")
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['company', 'requested_at']),
            models.Index(fields=['api_provider', 'model_name']),
            models.Index(fields=['success', 'requested_at']),
            models.Index(fields=['total_cost', 'requested_at']),
        ]
    
    def __str__(self):
        return f"{self.api_provider} - {self.model_name} (${self.total_cost})"
    
    def save(self, *args, **kwargs):
        """Auto-calcular total_tokens y total_cost si no están definidos"""
        if not self.total_tokens:
            self.total_tokens = self.input_tokens + self.output_tokens
        if not self.total_cost:
            self.total_cost = self.input_cost + self.output_cost
        super().save(*args, **kwargs)


class AIInsight(models.Model):
    """
    Almacenamiento de insights generados por AI
    Incluye sentiment analysis y strategy recommendations
    """
    
    INSIGHT_TYPES = [
        ('sentiment_analysis', 'Análisis de Sentimiento'),
        ('customer_behavior', 'Comportamiento del Cliente'),
        ('market_trend', 'Tendencia de Mercado'),
        ('demand_pattern', 'Patrón de Demanda'),
        ('pricing_strategy', 'Estrategia de Precios'),
        ('inventory_optimization', 'Optimización de Inventario'),
        ('risk_assessment', 'Evaluación de Riesgo'),
        ('opportunity_identification', 'Identificación de Oportunidades'),
        ('strategy_recommendation', 'Recomendación de Estrategia'),
        ('performance_analysis', 'Análisis de Performance'),
    ]
    
    CONFIDENCE_LEVELS = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('very_high', 'Muy Alta'),
    ]
    
    SENTIMENT_SCORES = [
        ('very_negative', 'Muy Negativo'),
        ('negative', 'Negativo'),
        ('neutral', 'Neutral'),
        ('positive', 'Positivo'),
        ('very_positive', 'Muy Positivo'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='ai_insights'
    )
    
    # Tipo y configuración
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=200, verbose_name="Título del insight")
    description = models.TextField(verbose_name="Descripción detallada")
    
    # Datos del insight
    insight_data = models.JSONField(default=dict, verbose_name="Datos estructurados del insight")
    raw_ai_response = models.TextField(verbose_name="Respuesta completa de AI")
    
    # Análisis de sentimiento (si aplica)
    sentiment_score = models.CharField(
        max_length=20, 
        choices=SENTIMENT_SCORES, 
        blank=True,
        verbose_name="Puntuación de sentimiento"
    )
    sentiment_confidence = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Recomendaciones estratégicas
    recommendations = models.JSONField(default=list, verbose_name="Recomendaciones")
    priority_level = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ],
        default='medium'
    )
    
    # Confianza y validación
    confidence_level = models.CharField(max_length=10, choices=CONFIDENCE_LEVELS, default='medium')
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Validación humana
    human_validated = models.BooleanField(default=False)
    validation_feedback = models.TextField(blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_insights'
    )
    
    # Métricas de impacto
    impact_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    business_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Relaciones con otros modelos
    related_customers = models.ManyToManyField(
        'inventory.Customer',
        blank=True,
        related_name='ai_insights'
    )
    related_products = models.ManyToManyField(
        'inventory.Product',
        blank=True,
        related_name='ai_insights'
    )
    
    # Tracking de implementación
    implemented = models.BooleanField(default=False)
    implementation_notes = models.TextField(blank=True)
    implementation_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    api_usage = models.ForeignKey(
        AIAPIUsage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_insights'
    )
    prompt_version = models.ForeignKey(
        AIPromptVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_insights'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_insights'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'insight_type']),
            models.Index(fields=['confidence_level', 'created_at']),
            models.Index(fields=['priority_level', 'implemented']),
            models.Index(fields=['sentiment_score', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_insight_type_display()})"


class HybridMLAIPrediction(models.Model):
    """
    Predicciones híbridas que combinan ML tradicional con AI insights
    Unifica los dos enfoques en una sola predicción
    """
    
    PREDICTION_TYPES = [
        ('demand_forecast', 'Pronóstico de Demanda'),
        ('customer_churn', 'Abandono de Cliente'),
        ('customer_clv', 'Valor de Vida del Cliente'),
        ('inventory_optimization', 'Optimización de Inventario'),
        ('pricing_optimization', 'Optimización de Precios'),
        ('market_expansion', 'Expansión de Mercado'),
        ('risk_assessment', 'Evaluación de Riesgo'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='hybrid_predictions'
    )
    
    # Tipo y configuración
    prediction_type = models.CharField(max_length=30, choices=PREDICTION_TYPES)
    name = models.CharField(max_length=200, verbose_name="Nombre de la predicción")
    description = models.TextField(blank=True)
    
    # Componente ML tradicional
    ml_model = models.ForeignKey(
        'ForecastModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hybrid_predictions'
    )
    ml_prediction = models.JSONField(default=dict, verbose_name="Predicción ML")
    ml_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Componente AI
    ai_insight = models.ForeignKey(
        AIInsight,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hybrid_predictions'
    )
    ai_prediction = models.JSONField(default=dict, verbose_name="Predicción AI")
    ai_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Predicción híbrida final
    final_prediction = models.JSONField(default=dict, verbose_name="Predicción final híbrida")
    hybrid_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Pesos de combinación
    ml_weight = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('0.5'),
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    ai_weight = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('0.5'),
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    # Validación y resultados
    actual_outcome = models.JSONField(default=dict, blank=True, verbose_name="Resultado real")
    accuracy_ml = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    accuracy_ai = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    accuracy_hybrid = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_hybrid_predictions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'prediction_type']),
            models.Index(fields=['hybrid_confidence', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} (Híbrido ML+AI)"
    
    def save(self, *args, **kwargs):
        """Validar que los pesos sumen 1.0"""
        if self.ml_weight + self.ai_weight != 1.0:
            # Normalizar pesos si no suman 1.0
            total = self.ml_weight + self.ai_weight
            if total > 0:
                self.ml_weight = self.ml_weight / total
                self.ai_weight = self.ai_weight / total
        super().save(*args, **kwargs)
