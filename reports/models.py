from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json


class ReportTemplate(models.Model):
    """Plantillas de reportes personalizables"""
    
    REPORT_TYPES = [
        ('inventory_summary', 'Resumen de Inventario'),
        ('stock_movement', 'Movimiento de Stock'),
        ('abc_analysis', 'Análisis ABC'),
        ('turnover_analysis', 'Análisis de Rotación'),
        ('forecast_accuracy', 'Precisión de Pronósticos'),
        ('alerts_summary', 'Resumen de Alertas'),
        ('supplier_performance', 'Rendimiento de Proveedores'),
        ('product_performance', 'Rendimiento de Productos'),
        ('cost_analysis', 'Análisis de Costos'),
        ('custom', 'Personalizado'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    FREQUENCY_CHOICES = [
        ('on_demand', 'Bajo demanda'),
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='report_templates'
    )
    name = models.CharField(max_length=200, verbose_name="Nombre del reporte")
    description = models.TextField(blank=True, verbose_name="Descripción")
    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPES,
        verbose_name="Tipo de reporte"
    )
    
    # Configuración del reporte
    default_format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default='pdf',
        verbose_name="Formato por defecto"
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='on_demand',
        verbose_name="Frecuencia"
    )
    
    # Filtros por defecto (JSON)
    default_filters = models.JSONField(
        default=dict,
        verbose_name="Filtros por defecto"
    )
    
    # Configuración de columnas y campos
    columns_config = models.JSONField(
        default=list,
        verbose_name="Configuración de columnas"
    )
    
    # Configuración de gráficos
    charts_config = models.JSONField(
        default=list,
        verbose_name="Configuración de gráficos"
    )
    
    # Configuración de agrupación y ordenamiento
    grouping_config = models.JSONField(
        default=dict,
        verbose_name="Configuración de agrupación"
    )
    sorting_config = models.JSONField(
        default=list,
        verbose_name="Configuración de ordenamiento"
    )
    
    # Configuración de distribución
    auto_send = models.BooleanField(default=False, verbose_name="Envío automático")
    recipients = models.ManyToManyField(
        'authentication.User',
        blank=True,
        verbose_name="Destinatarios"
    )
    additional_emails = models.TextField(
        blank=True,
        help_text="Emails adicionales separados por comas",
        verbose_name="Emails adicionales"
    )
    
    # Estado y metadatos
    is_active = models.BooleanField(default=True, verbose_name="Plantilla activa")
    is_system_template = models.BooleanField(default=False, verbose_name="Plantilla del sistema")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_report_templates'
    )
    
    class Meta:
        verbose_name = "Plantilla de reporte"
        verbose_name_plural = "Plantillas de reportes"
        ordering = ['-created_at']
        unique_together = [['company', 'name']]
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"
    
    def get_recipient_emails(self):
        """Obtiene todos los emails de destinatarios"""
        emails = []
        
        # Emails de usuarios
        for user in self.recipients.filter(is_active=True):
            if user.email:
                emails.append(user.email)
        
        # Emails adicionales
        if self.additional_emails:
            additional = [email.strip() for email in self.additional_emails.split(',')]
            emails.extend(additional)
        
        return list(set(emails))  # Eliminar duplicados


class Report(models.Model):
    """Reportes generados"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('generating', 'Generando'),
        ('completed', 'Completado'),
        ('failed', 'Falló'),
        ('sent', 'Enviado'),
    ]
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='generated_reports'
    )
    
    # Información básica
    title = models.CharField(max_length=200, verbose_name="Título del reporte")
    description = models.TextField(blank=True, verbose_name="Descripción")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )
    
    # Parámetros del reporte
    parameters = models.JSONField(
        default=dict,
        verbose_name="Parámetros del reporte"
    )
    filters_applied = models.JSONField(
        default=dict,
        verbose_name="Filtros aplicados"
    )
    
    # Período de datos
    date_from = models.DateField(verbose_name="Fecha desde")
    date_to = models.DateField(verbose_name="Fecha hasta")
    
    # Archivo generado
    file_format = models.CharField(max_length=20, verbose_name="Formato del archivo")
    file_path = models.CharField(max_length=500, blank=True, verbose_name="Ruta del archivo")
    file_size_mb = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Tamaño del archivo (MB)"
    )
    
    # Estadísticas del reporte
    total_records = models.PositiveIntegerField(null=True, blank=True, verbose_name="Total de registros")
    generation_time_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tiempo de generación (segundos)"
    )
    
    # Metadatos de ejecución
    error_message = models.TextField(blank=True, verbose_name="Mensaje de error")
    execution_log = models.TextField(blank=True, verbose_name="Log de ejecución")
    
    # Usuarios y fechas
    requested_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_reports'
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template', 'status']),
            models.Index(fields=['requested_by', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d')}"
    
    @property
    def is_expired(self):
        """Verifica si el reporte ha expirado"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False
    
    @property
    def download_url(self):
        """URL de descarga del reporte"""
        if self.status == 'completed' and self.file_path:
            return f"/api/reports/{self.id}/download/"
        return None


class KPIDefinition(models.Model):
    """Definiciones de KPIs para reportes"""
    
    CALCULATION_TYPES = [
        ('sum', 'Suma'),
        ('average', 'Promedio'),
        ('count', 'Conteo'),
        ('percentage', 'Porcentaje'),
        ('ratio', 'Ratio'),
        ('custom', 'Personalizado'),
    ]
    
    DATA_SOURCES = [
        ('inventory', 'Inventario'),
        ('transactions', 'Transacciones'),
        ('forecasts', 'Pronósticos'),
        ('alerts', 'Alertas'),
        ('products', 'Productos'),
        ('suppliers', 'Proveedores'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='kpi_definitions'
    )
    name = models.CharField(max_length=200, verbose_name="Nombre del KPI")
    description = models.TextField(verbose_name="Descripción")
    code = models.CharField(max_length=50, verbose_name="Código único")
    
    # Configuración del cálculo
    calculation_type = models.CharField(
        max_length=20,
        choices=CALCULATION_TYPES,
        verbose_name="Tipo de cálculo"
    )
    data_source = models.CharField(
        max_length=20,
        choices=DATA_SOURCES,
        verbose_name="Fuente de datos"
    )
    
    # Fórmula personalizada (para cálculos complejos)
    formula = models.TextField(
        blank=True,
        help_text="Fórmula SQL o expresión para cálculos personalizados",
        verbose_name="Fórmula"
    )
    
    # Configuración de filtros
    default_filters = models.JSONField(
        default=dict,
        verbose_name="Filtros por defecto"
    )
    
    # Configuración de formato
    unit = models.CharField(max_length=20, blank=True, verbose_name="Unidad")
    decimal_places = models.PositiveIntegerField(default=2, verbose_name="Decimales")
    show_as_percentage = models.BooleanField(default=False, verbose_name="Mostrar como porcentaje")
    
    # Umbrales para semáforos
    good_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Umbral bueno"
    )
    warning_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Umbral advertencia"
    )
    critical_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Umbral crítico"
    )
    
    # Configuración de tendencia
    track_trend = models.BooleanField(default=True, verbose_name="Seguir tendencia")
    trend_periods = models.PositiveIntegerField(default=12, verbose_name="Períodos de tendencia")
    
    # Estado y metadatos
    is_active = models.BooleanField(default=True, verbose_name="KPI activo")
    is_system_kpi = models.BooleanField(default=False, verbose_name="KPI del sistema")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Orden de visualización")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_kpi_definitions'
    )
    
    class Meta:
        verbose_name = "Definición de KPI"
        verbose_name_plural = "Definiciones de KPIs"
        ordering = ['sort_order', 'name']
        unique_together = [['company', 'code']]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_status_color(self, value):
        """Determina el color del semáforo basado en el valor"""
        if value is None:
            return 'gray'
        
        value = float(value)
        
        if self.good_threshold is not None and value >= float(self.good_threshold):
            return 'green'
        elif self.warning_threshold is not None and value >= float(self.warning_threshold):
            return 'yellow'
        elif self.critical_threshold is not None:
            return 'red'
        
        return 'gray'


class KPIValue(models.Model):
    """Valores calculados de KPIs"""
    
    kpi_definition = models.ForeignKey(
        KPIDefinition,
        on_delete=models.CASCADE,
        related_name='values'
    )
    
    # Período del valor
    period_start = models.DateField(verbose_name="Inicio del período")
    period_end = models.DateField(verbose_name="Fin del período")
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Diario'),
            ('weekly', 'Semanal'),
            ('monthly', 'Mensual'),
            ('quarterly', 'Trimestral'),
            ('yearly', 'Anual'),
        ],
        verbose_name="Tipo de período"
    )
    
    # Valor calculado
    value = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="Valor"
    )
    
    # Contexto adicional
    context_data = models.JSONField(
        default=dict,
        verbose_name="Datos de contexto"
    )
    
    # Metadatos de cálculo
    calculated_at = models.DateTimeField(auto_now_add=True)
    calculation_duration_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Duración del cálculo (ms)"
    )
    
    class Meta:
        verbose_name = "Valor de KPI"
        verbose_name_plural = "Valores de KPIs"
        ordering = ['-period_end']
        unique_together = [['kpi_definition', 'period_start', 'period_end']]
        indexes = [
            models.Index(fields=['kpi_definition', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.kpi_definition.name} - {self.period_end} - {self.value}"
    
    @property
    def status_color(self):
        """Color del semáforo para este valor"""
        return self.kpi_definition.get_status_color(self.value)


class ReportSchedule(models.Model):
    """Programación automática de reportes"""
    
    SCHEDULE_TYPES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
    ]
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    
    name = models.CharField(max_length=200, verbose_name="Nombre de la programación")
    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPES,
        verbose_name="Tipo de programación"
    )
    
    # Configuración de tiempo
    hour = models.PositiveIntegerField(
        default=9,
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        verbose_name="Hora"
    )
    minute = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(59)],
        verbose_name="Minuto"
    )
    
    # Para reportes semanales
    day_of_week = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text="0=Lunes, 6=Domingo",
        verbose_name="Día de la semana"
    )
    
    # Para reportes mensuales
    day_of_month = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Día del mes"
    )
    
    # Estado y control
    is_active = models.BooleanField(default=True, verbose_name="Programación activa")
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_run_status = models.CharField(max_length=20, blank=True, verbose_name="Estado última ejecución")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_report_schedules'
    )
    
    class Meta:
        verbose_name = "Programación de reporte"
        verbose_name_plural = "Programaciones de reportes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_schedule_type_display()}"
    
    def calculate_next_run(self):
        """Calcula la próxima fecha de ejecución"""
        from django.utils import timezone
        from datetime import datetime, timedelta
        import calendar
        
        now = timezone.now()
        next_run = None
        
        if self.schedule_type == 'daily':
            next_run = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif self.schedule_type == 'weekly' and self.day_of_week is not None:
            days_ahead = self.day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
        
        elif self.schedule_type == 'monthly' and self.day_of_month is not None:
            # Próximo mes si ya pasó el día en este mes
            if now.day >= self.day_of_month:
                next_month = now.replace(day=1) + timedelta(days=32)
                next_month = next_month.replace(day=1)
            else:
                next_month = now.replace(day=1)
            
            # Ajustar si el día no existe en el mes
            max_day = calendar.monthrange(next_month.year, next_month.month)[1]
            day = min(self.day_of_month, max_day)
            
            next_run = next_month.replace(
                day=day,
                hour=self.hour,
                minute=self.minute,
                second=0,
                microsecond=0
            )
        
        if next_run:
            self.next_run_at = next_run
            self.save(update_fields=['next_run_at'])


class ReportDistribution(models.Model):
    """Registro de distribución de reportes"""
    
    DISTRIBUTION_TYPES = [
        ('email', 'Email'),
        ('download', 'Descarga'),
        ('api', 'API'),
        ('ftp', 'FTP'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Falló'),
        ('delivered', 'Entregado'),
    ]
    
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='distributions'
    )
    distribution_type = models.CharField(
        max_length=20,
        choices=DISTRIBUTION_TYPES,
        verbose_name="Tipo de distribución"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )
    
    # Destinatarios
    recipients = models.JSONField(
        default=list,
        verbose_name="Lista de destinatarios"
    )
    
    # Tiempos
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Información adicional
    error_message = models.TextField(
        blank=True,
        verbose_name="Mensaje de error"
    )
    delivery_details = models.JSONField(
        default=dict,
        verbose_name="Detalles de entrega"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Distribución de reporte"
        verbose_name_plural = "Distribuciones de reportes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Distribution {self.id} - {self.report.title} ({self.distribution_type})"
    
    @property
    def recipient_count(self):
        """Número de destinatarios"""
        if isinstance(self.recipients, list):
            return len(self.recipients)
        return 0
