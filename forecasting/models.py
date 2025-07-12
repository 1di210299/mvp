from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json


class ForecastModel(models.Model):
    """Modelos de pronóstico de machine learning"""
    
    MODEL_TYPES = [
        ('prophet', 'Facebook Prophet'),
        ('arima', 'ARIMA'),
        ('linear_regression', 'Regresión Lineal'),
        ('random_forest', 'Random Forest'),
        ('lstm', 'LSTM Neural Network'),
    ]
    
    STATUS_CHOICES = [
        ('training', 'Entrenando'),
        ('active', 'Activo'),
        ('deprecated', 'Depreciado'),
        ('failed', 'Falló'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='forecast_models'
    )
    name = models.CharField(max_length=200, verbose_name="Nombre del modelo")
    description = models.TextField(blank=True, verbose_name="Descripción")
    model_type = models.CharField(
        max_length=50,
        choices=MODEL_TYPES,
        verbose_name="Tipo de modelo"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='training',
        verbose_name="Estado"
    )
    
    # Configuración del modelo
    products = models.ManyToManyField(
        'inventory.Product',
        blank=True,
        verbose_name="Productos aplicables"
    )
    categories = models.ManyToManyField(
        'inventory.Category',
        blank=True,
        verbose_name="Categorías aplicables"
    )
    
    # Parámetros del modelo
    forecast_horizon_days = models.PositiveIntegerField(
        default=30,
        verbose_name="Horizonte de pronóstico (días)"
    )
    training_period_days = models.PositiveIntegerField(
        default=365,
        verbose_name="Período de entrenamiento (días)"
    )
    confidence_interval = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('95.00'),
        validators=[MinValueValidator(50), MaxValueValidator(99.99)],
        verbose_name="Intervalo de confianza (%)"
    )
    
    # Hiperparámetros específicos del modelo (JSON)
    hyperparameters = models.JSONField(
        default=dict,
        verbose_name="Hiperparámetros"
    )
    
    # Métricas de rendimiento
    mae = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Error Absoluto Medio"
    )
    mape = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True,  # Make sure this is True
        blank=True,  # Make sure this is True
        verbose_name="Error Porcentual Absoluto Medio"
    )
    rmse = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Raíz del Error Cuadrático Medio"
    )
    r2_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Coeficiente de Determinación R²"
    )
    
    # Archivos del modelo
    model_file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Ruta del archivo del modelo"
    )
    model_size_mb = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Tamaño del modelo (MB)"
    )
    
    # Versioning
    version = models.CharField(max_length=20, default="1.0", verbose_name="Versión")
    parent_model = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_models',
        verbose_name="Modelo padre"
    )
    
    # Metadatos
    training_started_at = models.DateTimeField(null=True, blank=True)
    training_completed_at = models.DateTimeField(null=True, blank=True)
    last_prediction_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_forecast_models'
    )
    
    class Meta:
        verbose_name = "Modelo de pronóstico"
        verbose_name_plural = "Modelos de pronóstico"
        ordering = ['-created_at']
        unique_together = [['company', 'name', 'version']]
    
    def __str__(self):
        return f"{self.name} v{self.version} - {self.get_model_type_display()}"
    
    @property
    def accuracy_score(self):
        """Calcula un score de precisión basado en MAPE"""
        if self.mape is not None:
            return max(0, 100 - float(self.mape))
        return None
    
    @property
    def training_duration(self):
        """Duración del entrenamiento"""
        if self.training_started_at and self.training_completed_at:
            return self.training_completed_at - self.training_started_at
        return None


class DemandForecast(models.Model):
    """Pronósticos de demanda generados"""
    
    FORECAST_TYPES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
    ]
    
    model = models.ForeignKey(
        ForecastModel,
        on_delete=models.CASCADE,
        related_name='forecasts'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='demand_forecasts'
    )
    location = models.ForeignKey(
        'inventory.Location',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='demand_forecasts'
    )
    
    # Período del pronóstico
    forecast_date = models.DateField(verbose_name="Fecha del pronóstico")
    forecast_type = models.CharField(
        max_length=20,
        choices=FORECAST_TYPES,
        default='daily',
        verbose_name="Tipo de pronóstico"
    )
    
    # Valores del pronóstico
    predicted_demand = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Demanda pronosticada"
    )
    lower_bound = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Límite inferior"
    )
    upper_bound = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Límite superior"
    )
    confidence_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Nivel de confianza"
    )
    
    # Datos contextuales
    seasonality_factor = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Factor de estacionalidad"
    )
    trend_factor = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Factor de tendencia"
    )
    
    # Factores externos (JSON)
    external_factors = models.JSONField(
        default=dict,
        verbose_name="Factores externos"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pronóstico de demanda"
        verbose_name_plural = "Pronósticos de demanda"
        ordering = ['forecast_date', 'product']
        unique_together = [['product', 'forecast_date', 'forecast_type', 'location']]
        indexes = [
            models.Index(fields=['product', 'forecast_date']),
            models.Index(fields=['forecast_date', 'forecast_type']),
        ]
    
    def __str__(self):
        return f"{self.product.sku} - {self.forecast_date} - {self.predicted_demand}"
    
    @property
    def forecast_range(self):
        """Rango del pronóstico"""
        return self.upper_bound - self.lower_bound
    
    @property
    def uncertainty_percentage(self):
        """Porcentaje de incertidumbre"""
        if self.predicted_demand > 0:
            return (self.forecast_range / self.predicted_demand) * 100
        return 0


class ForecastAccuracy(models.Model):
    """Seguimiento de la precisión de los pronósticos"""
    
    forecast = models.OneToOneField(
        DemandForecast,
        on_delete=models.CASCADE,
        related_name='accuracy'
    )
    
    # Valores reales observados
    actual_demand = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Demanda real"
    )
    
    # Métricas de error
    absolute_error = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Error absoluto"
    )
    percentage_error = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        verbose_name="Error porcentual"
    )
    squared_error = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="Error cuadrático"
    )
    
    # Indicadores de precisión
    within_bounds = models.BooleanField(
        verbose_name="Dentro de los límites"
    )
    bias = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Sesgo"
    )
    
    # Metadatos
    evaluated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Precisión del pronóstico"
        verbose_name_plural = "Precisiones de pronósticos"
        ordering = ['-evaluated_at']
    
    def __str__(self):
        return f"{self.forecast} - Error: {self.percentage_error}%"
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente las métricas de error"""
        predicted = self.forecast.predicted_demand
        actual = self.actual_demand
        
        self.absolute_error = abs(predicted - actual)
        
        if actual != 0:
            self.percentage_error = (self.absolute_error / abs(actual)) * 100
            self.bias = (predicted - actual) / actual * 100
        else:
            self.percentage_error = 0 if predicted == 0 else float('inf')
            self.bias = 0 if predicted == 0 else float('inf')
        
        self.squared_error = (predicted - actual) ** 2
        
        self.within_bounds = (
            self.forecast.lower_bound <= actual <= self.forecast.upper_bound
        )
        
        super().save(*args, **kwargs)


class ReorderRecommendation(models.Model):
    """Recomendaciones de reabastecimiento"""
    
    PRIORITY_LEVELS = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('ordered', 'Ordenada'),
        ('received', 'Recibida'),
        ('cancelled', 'Cancelada'),
    ]
    
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name='reorder_recommendations'
    )
    location = models.ForeignKey(
        'inventory.Location',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reorder_recommendations'
    )
    
    # Cantidades recomendadas
    recommended_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Cantidad recomendada"
    )
    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Stock actual"
    )
    projected_demand = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Demanda proyectada"
    )
    
    # Fechas y timing
    recommended_order_date = models.DateField(
        verbose_name="Fecha recomendada de orden"
    )
    expected_stockout_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha esperada de agotamiento"
    )
    lead_time_days = models.PositiveIntegerField(
        verbose_name="Tiempo de entrega (días)"
    )
    
    # Prioridad y estado
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_LEVELS,
        default='medium',
        verbose_name="Prioridad"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )
    
    # Costos estimados
    estimated_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Costo estimado"
    )
    potential_lost_sales = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Ventas potenciales perdidas"
    )
    
    # Referencias
    forecast_model = models.ForeignKey(
        ForecastModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reorder_recommendations'
    )
    
    # Notas y observaciones
    notes = models.TextField(blank=True, verbose_name="Notas")
    justification = models.TextField(
        blank=True,
        verbose_name="Justificación de la recomendación"
    )
    
    # Usuarios relacionados
    approved_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_reorder_recommendations'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Recomendación de reorden"
        verbose_name_plural = "Recomendaciones de reorden"
        ordering = ['-priority', 'recommended_order_date']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['recommended_order_date', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.product.sku} - {self.recommended_quantity} - {self.get_priority_display()}"
    
    @property
    def days_until_stockout(self):
        """Días hasta el agotamiento estimado"""
        if self.expected_stockout_date:
            from django.utils import timezone
            delta = self.expected_stockout_date - timezone.now().date()
            return delta.days
        return None
    
    @property
    def is_urgent(self):
        """Determina si la recomendación es urgente"""
        days_left = self.days_until_stockout
        return days_left is not None and days_left <= self.lead_time_days


class ModelTrainingJob(models.Model):
    """Registro de trabajos de entrenamiento de modelos"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('running', 'Ejecutando'),
        ('completed', 'Completado'),
        ('failed', 'Falló'),
        ('cancelled', 'Cancelado'),
    ]
    
    model = models.ForeignKey(
        ForecastModel,
        on_delete=models.CASCADE,
        related_name='training_jobs'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )
    
    # Tiempos de ejecución
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Resultados
    metrics = models.JSONField(
        default=dict,
        verbose_name="Métricas obtenidas"
    )
    error_message = models.TextField(
        blank=True,
        verbose_name="Mensaje de error"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_training_jobs'
    )
    
    class Meta:
        verbose_name = "Trabajo de entrenamiento"
        verbose_name_plural = "Trabajos de entrenamiento"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Training Job {self.id} - {self.model.name} ({self.status})"
    
    @property
    def duration(self):
        """Duración del trabajo de entrenamiento"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def duration_seconds(self):
        """Duración en segundos"""
        duration = self.duration
        if duration:
            return duration.total_seconds()
        return None
