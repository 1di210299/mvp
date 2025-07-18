"""
FORECASTING ML CORE MODELS - Foundation Architecture
====================================================

Modelos centrales para sistema ML escalable con:
- Versionado de modelos
- Sistema de métricas unificado
- Relaciones optimizadas para ML
- Índices de performance
- Arquitectura ML-first

Autor: Sistema ML Forecasting
Fecha: 2025-01-17
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from decimal import Decimal
import uuid


class MLModelVersion(models.Model):
    """
    Sistema de versionado para modelos ML
    Permite tracking de evolución de modelos y rollback
    """
    
    DEPLOYMENT_STATUS = [
        ('development', 'Desarrollo'),
        ('testing', 'Pruebas'),
        ('staging', 'Staging'),
        ('production', 'Producción'),
        ('deprecated', 'Depreciado'),
        ('archived', 'Archivado'),
    ]
    
    # Identificación única
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relación con modelo base
    forecast_model = models.ForeignKey(
        'ForecastModel',
        on_delete=models.CASCADE,
        related_name='versions'
    )
    
    # Versionado
    version = models.CharField(max_length=20, verbose_name="Versión (ej: 1.0.0)")
    parent_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_versions'
    )
    
    # Estado del deployment
    deployment_status = models.CharField(
        max_length=20,
        choices=DEPLOYMENT_STATUS,
        default='development'
    )
    is_active = models.BooleanField(default=False)
    
    # Metadata del modelo
    model_binary = models.BinaryField(null=True, blank=True)  # Modelo serializado
    model_path = models.CharField(max_length=500, blank=True)  # Path en storage
    model_size_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    # Performance metrics
    training_accuracy = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    validation_accuracy = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    test_accuracy = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    
    # Training metadata
    training_start = models.DateTimeField(null=True)
    training_end = models.DateTimeField(null=True)
    training_duration_seconds = models.PositiveIntegerField(null=True)
    training_samples = models.PositiveIntegerField(null=True)
    
    # Cambios y notas
    changelog = models.TextField(blank=True, verbose_name="Registro de cambios")
    notes = models.TextField(blank=True, verbose_name="Notas técnicas")
    
    # Audit trail
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ml_versions'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_ml_versions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['forecast_model', 'version']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['forecast_model', 'deployment_status']),
            models.Index(fields=['is_active', 'deployment_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.forecast_model.name} v{self.version} ({self.deployment_status})"


class MLMetric(models.Model):
    """
    Sistema unificado de métricas ML
    Almacena todas las métricas de performance de modelos
    """
    
    METRIC_TYPES = [
        # Regression metrics
        ('mae', 'Error Absoluto Medio'),
        ('mse', 'Error Cuadrático Medio'),
        ('rmse', 'Raíz del Error Cuadrático Medio'),
        ('mape', 'Error Porcentual Absoluto Medio'),
        ('r2', 'Coeficiente de Determinación'),
        
        # Classification metrics
        ('accuracy', 'Precisión'),
        ('precision', 'Precisión Positiva'),
        ('recall', 'Recall'),
        ('f1_score', 'Puntaje F1'),
        ('auc_roc', 'Área bajo ROC'),
        
        # Business metrics
        ('revenue_impact', 'Impacto en Ingresos'),
        ('cost_reduction', 'Reducción de Costos'),
        ('forecast_accuracy', 'Precisión de Pronóstico'),
        
        # Custom metrics
        ('custom', 'Métrica Personalizada'),
    ]
    
    METRIC_CONTEXT = [
        ('training', 'Entrenamiento'),
        ('validation', 'Validación'),
        ('test', 'Prueba'),
        ('production', 'Producción'),
    ]
    
    # Relaciones
    model_version = models.ForeignKey(
        'MLModelVersion',
        on_delete=models.CASCADE,
        related_name='metrics'
    )
    
    # Métrica
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    metric_name = models.CharField(max_length=100)  # Para métricas custom
    metric_value = models.DecimalField(max_digits=15, decimal_places=6)
    metric_context = models.CharField(max_length=20, choices=METRIC_CONTEXT)
    
    # Metadata
    calculation_date = models.DateTimeField(auto_now_add=True)
    dataset_size = models.PositiveIntegerField(null=True)
    time_period_start = models.DateTimeField(null=True)
    time_period_end = models.DateTimeField(null=True)
    
    # Configuración de la métrica
    metric_config = models.JSONField(default=dict)  # Parámetros de cálculo
    
    class Meta:
        ordering = ['-calculation_date']
        indexes = [
            models.Index(fields=['model_version', 'metric_type']),
            models.Index(fields=['metric_type', 'calculation_date']),
            models.Index(fields=['model_version', 'metric_context']),
        ]
    
    def __str__(self):
        return f"{self.metric_type}: {self.metric_value} ({self.metric_context})"


class MLExperiment(models.Model):
    """
    Tracking de experimentos ML
    Permite comparar diferentes configuraciones y algoritmos
    """
    
    EXPERIMENT_STATUS = [
        ('planning', 'Planificando'),
        ('running', 'Ejecutando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    # Identificación
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    experiment_id = models.CharField(max_length=50, unique=True)  # Para tracking externo
    
    # Relaciones
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='ml_experiments'
    )
    base_model = models.ForeignKey(
        'ForecastModel',
        on_delete=models.CASCADE,
        related_name='experiments'
    )
    
    # Estado
    status = models.CharField(max_length=20, choices=EXPERIMENT_STATUS, default='planning')
    
    # Configuración del experimento
    algorithms_tested = models.JSONField(default=list)  # ['prophet', 'arima', 'lstm']
    hyperparameters = models.JSONField(default=dict)  # Configuraciones probadas
    dataset_config = models.JSONField(default=dict)  # Configuración de datos
    
    # Resultados
    best_algorithm = models.CharField(max_length=50, blank=True)
    best_metric_value = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    winning_config = models.JSONField(default=dict)
    
    # Timing
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    duration_minutes = models.PositiveIntegerField(null=True)
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['base_model', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Experimento: {self.name} ({self.status})"


class MLModelRegistry(models.Model):
    """
    Registro centralizado de modelos ML
    Control de deployment y governance
    """
    
    GOVERNANCE_STATUS = [
        ('pending_review', 'Pendiente de Revisión'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('requires_changes', 'Requiere Cambios'),
    ]
    
    # Modelo registrado
    model_version = models.OneToOneField(
        'MLModelVersion',
        on_delete=models.CASCADE,
        related_name='registry_entry'
    )
    
    # Governance
    governance_status = models.CharField(max_length=30, choices=GOVERNANCE_STATUS)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviewed_models'
    )
    review_notes = models.TextField(blank=True)
    review_date = models.DateTimeField(null=True)
    
    # Compliance y validación
    passes_validation = models.BooleanField(default=False)
    validation_report = models.JSONField(default=dict)
    compliance_checks = models.JSONField(default=dict)
    
    # Performance thresholds
    min_accuracy_threshold = models.DecimalField(max_digits=6, decimal_places=4)
    current_accuracy = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    performance_degradation_alert = models.BooleanField(default=False)
    
    # Deployment tracking
    deployed_to_production = models.BooleanField(default=False)
    deployment_date = models.DateTimeField(null=True)
    rollback_plan = models.TextField(blank=True)
    
    # Monitoring
    last_health_check = models.DateTimeField(null=True)
    health_status = models.CharField(max_length=20, default='unknown')
    monitoring_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['governance_status']),
            models.Index(fields=['deployed_to_production']),
            models.Index(fields=['performance_degradation_alert']),
        ]
    
    def __str__(self):
        return f"Registry: {self.model_version} ({self.governance_status})"


class MLDatasetVersion(models.Model):
    """
    Versionado de datasets para reproducibilidad
    """
    
    # Dataset identification
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    
    # Relaciones
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='ml_datasets'
    )
    
    # Dataset metadata
    total_samples = models.PositiveIntegerField()
    training_samples = models.PositiveIntegerField()
    validation_samples = models.PositiveIntegerField()
    test_samples = models.PositiveIntegerField()
    
    # Data quality metrics
    missing_values_percent = models.DecimalField(max_digits=5, decimal_places=2)
    outliers_percent = models.DecimalField(max_digits=5, decimal_places=2)
    data_quality_score = models.DecimalField(max_digits=4, decimal_places=2)
    
    # Time range
    data_start_date = models.DateTimeField()
    data_end_date = models.DateTimeField()
    
    # Features
    feature_columns = models.JSONField(default=list)
    target_columns = models.JSONField(default=list)
    feature_engineering_steps = models.JSONField(default=list)
    
    # Storage
    dataset_path = models.CharField(max_length=500)
    dataset_size_mb = models.DecimalField(max_digits=10, decimal_places=2)
    checksum = models.CharField(max_length=64)  # SHA-256
    
    # Lineage
    source_datasets = models.ManyToManyField('self', blank=True)
    transformation_pipeline = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['name', 'version', 'company']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'name']),
            models.Index(fields=['data_start_date', 'data_end_date']),
        ]
    
    def __str__(self):
        return f"Dataset: {self.name} v{self.version}"
