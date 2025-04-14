# api/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class DataConnection(models.Model):
    """Model for storing connection information to data sources"""
    CONNECTION_TYPES = (
        ('file', 'File Upload'),
        ('sql', 'SQL Database'),
        ('api', 'External API'),
        ('s3', 'AWS S3 Bucket'),
    )
    
    name = models.CharField(max_length=255)
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPES)
    connection_string = models.CharField(max_length=1000, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    query = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections', null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.connection_type})"

class Dataset(models.Model):
    """Model for datasets in the system"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    connection = models.ForeignKey(DataConnection, on_delete=models.SET_NULL, null=True, blank=True)
    columns = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class Analysis(models.Model):
    """Model for storing analysis results"""
    ANALYSIS_TYPES = (
        ('prediction', 'Sales Prediction'),
        ('segmentation', 'Customer Segmentation'),
        ('sentiment', 'Sentiment Analysis'),
        ('general', 'General Analysis'),
    )
    
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='analyses')
    name = models.CharField(max_length=255)
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES)
    parameters = models.JSONField(default=dict, blank=True)
    results = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Analyses'
    
    def __str__(self):
        return f"{self.name} ({self.analysis_type}) for {self.dataset.name}"
    

# Añadir al final de api/models.py

from django.db import models
from django.contrib.auth.models import User

class BusinessRule(models.Model):
    """
    Reglas de negocio configurables para la toma de decisiones autónoma
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    rule_type = models.CharField(max_length=50, choices=[
        ('threshold', 'Umbral'),
        ('anomaly', 'Anomalía'),
        ('opportunity', 'Oportunidad'),
        ('risk', 'Riesgo')
    ])
    metric = models.CharField(max_length=100)  # Métrica a monitorear (ventas, inventario, etc.)
    condition = models.CharField(max_length=50, choices=[
        ('gt', 'Mayor que'),
        ('lt', 'Menor que'),
        ('eq', 'Igual a'),
        ('change', 'Cambio porcentual')
    ])
    threshold_value = models.FloatField()  # Valor umbral para activar la regla
    action_type = models.CharField(max_length=50, choices=[
        ('notify', 'Notificar'),
        ('suggest', 'Sugerir acción'),
        ('auto', 'Ejecutar automáticamente')
    ])
    action_data = models.JSONField(default=dict)  # Configuración de la acción a realizar
    priority = models.IntegerField(default=5)  # 1-10, siendo 10 la mayor prioridad
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_rules')

    def __str__(self):
        return self.name

class MonitoringLog(models.Model):
    """
    Registro de las actividades de monitoreo y acciones del agente
    """
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE, related_name='monitoring_logs')
    rule = models.ForeignKey(BusinessRule, on_delete=models.SET_NULL, null=True, blank=True)
    log_type = models.CharField(max_length=50, choices=[
        ('anomaly', 'Anomalía detectada'),
        ('opportunity', 'Oportunidad identificada'),
        ('action', 'Acción tomada'),
        ('alert', 'Alerta generada')
    ])
    description = models.TextField()
    metrics = models.JSONField(default=dict)  # Métricas relevantes en el momento del log
    created_at = models.DateTimeField(auto_now_add=True)
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica')
    ], default='medium')
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, null=True)
    resolution_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.log_type} - {self.created_at}"

class AgentAction(models.Model):
    """
    Acciones realizadas o sugeridas por el agente
    """
    action_type = models.CharField(max_length=50, choices=[
        ('price_change', 'Cambio de precio'),
        ('inventory', 'Gestión de inventario'),
        ('marketing', 'Campaña de marketing'),
        ('customer', 'Acción con cliente'),
        ('financial', 'Acción financiera'),
        ('operational', 'Acción operativa')
    ])
    status = models.CharField(max_length=20, choices=[
        ('suggested', 'Sugerida'),
        ('pending', 'Pendiente de aprobación'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('executed', 'Ejecutada'),
        ('failed', 'Fallida')
    ], default='suggested')
    description = models.TextField()
    action_data = models.JSONField()  # Detalles específicos de la acción
    expected_impact = models.TextField(blank=True, null=True)  # Impacto esperado
    confidence = models.FloatField(default=0.0)  # Confianza en la recomendación (0-1)
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    result_notes = models.TextField(blank=True, null=True)  # Resultados tras la ejecución
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE, related_name='agent_actions')
    rule = models.ForeignKey(BusinessRule, on_delete=models.SET_NULL, null=True, blank=True)
    monitoring_log = models.ForeignKey(MonitoringLog, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.action_type}: {self.description[:50]}"

class BusinessContext(models.Model):
    """
    Contexto de negocio para enriquecer las decisiones del agente
    """
    name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=100)  # Sector/industria
    region = models.CharField(max_length=100)  # Región del Perú
    seasonality_data = models.JSONField(default=dict)  # Patrones estacionales
    market_trends = models.JSONField(default=dict)  # Tendencias del mercado
    external_factors = models.JSONField(default=dict)  # Factores externos relevantes
    key_metrics = models.JSONField(default=dict)  # Métricas clave para este contexto
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_contexts')

    def __str__(self):
        return f"{self.name} - {self.business_type} ({self.region})"

class AgentLearningLog(models.Model):
    """
    Registro de aprendizaje del agente basado en acciones pasadas
    """
    action = models.ForeignKey(AgentAction, on_delete=models.CASCADE, related_name='learning_logs')
    success_score = models.FloatField()  # Evaluación del éxito (-1 a 1)
    metrics_before = models.JSONField()  # Métricas antes de la acción
    metrics_after = models.JSONField()  # Métricas después de la acción
    insights = models.TextField()  # Insights generados
    created_at = models.DateTimeField(auto_now_add=True)
    feedback_source = models.CharField(max_length=50, choices=[
        ('auto', 'Automático basado en métricas'),
        ('user', 'Feedback del usuario'),
        ('hybrid', 'Combinado')
    ])
    applied_to_model = models.BooleanField(default=False)  # Si se usó para reentrenar el modelo

    def __str__(self):
        return f"Aprendizaje de {self.action}: {self.success_score}"