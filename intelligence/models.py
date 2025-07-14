from django.db import models
from django.contrib.auth import get_user_model
from authentication.models import Company
import json

User = get_user_model()

class IntelligenceBriefing(models.Model):
    """Modelo para almacenar briefings matutinos generados por IA"""
    
    BRIEFING_TYPES = [
        ('morning', 'Briefing Matutino'),
        ('weekly', 'Reporte Semanal'),
        ('monthly', 'Reporte Mensual'),
        ('custom', 'Personalizado')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='briefings')
    briefing_type = models.CharField(max_length=20, choices=BRIEFING_TYPES, default='morning')
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contenido del briefing
    greeting = models.TextField()
    summary = models.TextField()
    priorities_json = models.JSONField(default=list)  # Top priorities
    opportunities_json = models.JSONField(default=list)  # Opportunities
    recommendations_json = models.JSONField(default=list)  # Recommendations
    metrics_json = models.JSONField(default=dict)  # Contextual metrics
    
    # Metadatos
    data_snapshot_json = models.JSONField(default=dict)  # Datos usados para generar el briefing
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'intelligence_briefing'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['company', 'briefing_type']),
            models.Index(fields=['generated_at']),
        ]

    def __str__(self):
        return f"{self.get_briefing_type_display()} - {self.company.name} - {self.generated_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def priorities(self):
        """Getter para priorities como lista de objetos"""
        return self.priorities_json

    @property
    def opportunities(self):
        """Getter para opportunities como lista de objetos"""
        return self.opportunities_json

    @property
    def recommendations(self):
        """Getter para recommendations como lista de objetos"""
        return self.recommendations_json

    @property
    def metrics(self):
        """Getter para metrics como diccionario"""
        return self.metrics_json

    @property
    def data_snapshot(self):
        """Getter para data_snapshot como diccionario"""
        return self.data_snapshot_json

class IntelligenceInsight(models.Model):
    """Modelo para almacenar insights específicos generados por IA"""
    
    INSIGHT_TYPES = [
        ('priority', 'Prioridad'),
        ('opportunity', 'Oportunidad'),
        ('recommendation', 'Recomendación'),
        ('trend', 'Tendencia'),
        ('warning', 'Advertencia'),
        ('forecast', 'Pronóstico')
    ]
    
    PRIORITY_LEVELS = [
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='insights')
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    actions_json = models.JSONField(default=list)  # Lista de acciones recomendadas
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Datos contextuales
    source_data_json = models.JSONField(default=dict)  # Datos que generaron este insight
    confidence_score = models.FloatField(default=0.0)  # Confianza del insight (0-100)
    
    class Meta:
        db_table = 'intelligence_insight'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'insight_type']),
            models.Index(fields=['priority', 'is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_insight_type_display()} - {self.title} - {self.company.name}"

    @property
    def actions(self):
        """Getter para actions como lista"""
        return self.actions_json

    @property
    def source_data(self):
        """Getter para source_data como diccionario"""
        return self.source_data_json

class IntelligenceMetric(models.Model):
    """Modelo para almacenar métricas calculadas por IA"""
    
    METRIC_TYPES = [
        ('sales_trend', 'Tendencia de Ventas'),
        ('inventory_health', 'Salud del Inventario'),
        ('customer_behavior', 'Comportamiento del Cliente'),
        ('supplier_performance', 'Rendimiento de Proveedores'),
        ('profit_margin', 'Margen de Ganancia'),
        ('forecast_accuracy', 'Precisión de Pronósticos')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='intelligence_metrics')
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    
    # Valores de la métrica
    current_value = models.FloatField()
    previous_value = models.FloatField(null=True, blank=True)
    change_percentage = models.FloatField(null=True, blank=True)
    trend = models.CharField(max_length=10, choices=[('up', 'Subiendo'), ('down', 'Bajando'), ('stable', 'Estable')], default='stable')
    
    # Contexto temporal
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    comparison_period_start = models.DateTimeField(null=True, blank=True)
    comparison_period_end = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    calculated_at = models.DateTimeField(auto_now_add=True)
    calculation_method = models.CharField(max_length=100)  # Método usado para calcular
    raw_data_json = models.JSONField(default=dict)  # Datos brutos usados
    
    class Meta:
        db_table = 'intelligence_metric'
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['company', 'metric_type']),
            models.Index(fields=['calculated_at']),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.company.name} - {self.calculated_at.strftime('%Y-%m-%d')}"

    @property
    def raw_data(self):
        """Getter para raw_data como diccionario"""
        return self.raw_data_json
