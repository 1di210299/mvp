from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class AlertRule(models.Model):
    """Reglas de alertas configurables"""
    
    ALERT_TYPES = [
        ('low_stock', 'Stock bajo'),
        ('high_stock', 'Stock alto'),
        ('expiration', 'Próximo a vencer'),
        ('expired', 'Vencido'),
        ('high_demand', 'Demanda alta'),
        ('no_movement', 'Sin movimiento'),
        ('negative_stock', 'Stock negativo'),
    ]
    
    FREQUENCY_CHOICES = [
        ('immediate', 'Inmediata'),
        ('daily', 'Diaria'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )
    name = models.CharField(max_length=200, verbose_name="Nombre de la regla")
    description = models.TextField(blank=True, verbose_name="Descripción")
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPES,
        verbose_name="Tipo de alerta"
    )
    
    # Configuración de la regla
    threshold_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor umbral"
    )
    threshold_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Porcentaje umbral"
    )
    days_before_expiration = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Días antes del vencimiento"
    )
    
    # Filtros
    categories = models.ManyToManyField(
        'inventory.Category',
        blank=True,
        verbose_name="Categorías aplicables"
    )
    products = models.ManyToManyField(
        'inventory.Product',
        blank=True,
        verbose_name="Productos específicos"
    )
    locations = models.ManyToManyField(
        'inventory.Location',
        blank=True,
        verbose_name="Ubicaciones específicas"
    )
    
    # Configuración de notificaciones
    send_email = models.BooleanField(default=True, verbose_name="Enviar email")
    send_notification = models.BooleanField(default=True, verbose_name="Enviar notificación")
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='immediate',
        verbose_name="Frecuencia"
    )
    
    # Destinatarios
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
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Regla activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_alert_rules'
    )
    
    class Meta:
        verbose_name = "Regla de alerta"
        verbose_name_plural = "Reglas de alertas"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_alert_type_display()}"
    
    def get_recipient_emails(self):
        """Obtiene todos los emails de destinatarios"""
        emails = []
        
        # Emails de usuarios
        for user in self.recipients.filter(is_active=True):
            if user.email and user.email_notifications:
                emails.append(user.email)
        
        # Emails adicionales
        if self.additional_emails:
            additional = [email.strip() for email in self.additional_emails.split(',')]
            emails.extend(additional)
        
        return list(set(emails))  # Eliminar duplicados


class Alert(models.Model):
    """Alertas generadas por el sistema"""
    
    SEVERITY_LEVELS = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('acknowledged', 'Reconocida'),
        ('resolved', 'Resuelta'),
        ('dismissed', 'Descartada'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    rule = models.ForeignKey(
        AlertRule,
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    
    title = models.CharField(max_length=200, verbose_name="Título")
    message = models.TextField(verbose_name="Mensaje")
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='medium',
        verbose_name="Severidad"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Estado"
    )
    
    # Contexto de la alerta
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    location = models.ForeignKey(
        'inventory.Location',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    current_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor actual"
    )
    threshold_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor umbral"
    )
    
    # Metadatos adicionales
    context_data = models.JSONField(default=dict, verbose_name="Datos de contexto")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Usuarios relacionados
    acknowledged_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    resolved_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    
    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'severity']),
            models.Index(fields=['product', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_severity_display()}"
    
    def acknowledge(self, user):
        """Marcar alerta como reconocida"""
        if self.status == 'active':
            self.status = 'acknowledged'
            self.acknowledged_by = user
            self.acknowledged_at = models.timezone.now()
            self.save()
    
    def resolve(self, user):
        """Marcar alerta como resuelta"""
        if self.status in ['active', 'acknowledged']:
            self.status = 'resolved'
            self.resolved_by = user
            self.resolved_at = models.timezone.now()
            self.save()
    
    def dismiss(self, user):
        """Descartar alerta"""
        if self.status in ['active', 'acknowledged']:
            self.status = 'dismissed'
            self.resolved_by = user
            self.resolved_at = models.timezone.now()
            self.save()


class NotificationLog(models.Model):
    """Log de notificaciones enviadas"""
    
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('in_app', 'En aplicación'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviada'),
        ('failed', 'Falló'),
        ('delivered', 'Entregada'),
    ]
    
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='notification_logs'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name="Tipo de notificación"
    )
    recipient = models.CharField(max_length=200, verbose_name="Destinatario")
    subject = models.CharField(max_length=200, blank=True, verbose_name="Asunto")
    content = models.TextField(verbose_name="Contenido")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )
    
    # Detalles del envío
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, verbose_name="Mensaje de error")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Log de notificación"
        verbose_name_plural = "Logs de notificaciones"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient} - {self.status}"
