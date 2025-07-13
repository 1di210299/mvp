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
        ('high_demand', 'Demanda alta proyectada'),
        ('demand_vs_stock', 'Demanda vs Stock insuficiente'),
        ('stockout_risk', 'Riesgo de agotamiento'),
        ('reorder_urgent', 'Reorden urgente'),
        ('forecast_accuracy', 'Precisión de pronóstico baja'),
        ('seasonal_demand', 'Demanda estacional'),
        ('no_movement', 'Sin movimiento'),
        ('negative_stock', 'Stock negativo'),
        ('inventory_value', 'Valor de inventario alto/bajo'),
        ('supplier_delay', 'Retraso de proveedor'),
        ('abc_analysis', 'Análisis ABC - Atención requerida'),
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
        max_length=30,  # Aumentado para nuevos tipos
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
    
    # Nuevos campos para alertas de forecasting
    forecast_horizon_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=7,
        verbose_name="Horizonte de pronóstico (días)"
    )
    accuracy_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Umbral de precisión (%)",
        help_text="Para alertas de precisión de pronóstico"
    )
    seasonal_factor_threshold = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Factor estacional umbral",
        help_text="Para alertas de demanda estacional"
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
    send_whatsapp = models.BooleanField(default=False, verbose_name="Enviar WhatsApp")
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
    additional_phones = models.TextField(
        blank=True,
        help_text="Números de WhatsApp adicionales separados por comas (formato: +51999999999)",
        verbose_name="Teléfonos WhatsApp adicionales"
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

    def get_recipient_phones(self):
        """Obtiene todos los números de WhatsApp de destinatarios"""
        phones = []
        
        # Números de usuarios
        for user in self.recipients.filter(is_active=True):
            if user.phone and user.whatsapp_notifications:
                # Normalizar número de teléfono
                phone = self.normalize_phone_number(user.phone)
                if phone:
                    phones.append(phone)
        
        # Números adicionales
        if self.additional_phones:
            additional = [self.normalize_phone_number(phone.strip()) 
                         for phone in self.additional_phones.split(',')]
            phones.extend([phone for phone in additional if phone])
        
        return list(set(phones))  # Eliminar duplicados

    @staticmethod
    def normalize_phone_number(phone):
        """Normaliza un número de teléfono para WhatsApp"""
        if not phone:
            return None
        
        # Limpiar el número
        import re
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Si no empieza con +, agregar código de país por defecto
        if not phone.startswith('+'):
            if phone.startswith('9'):  # Número peruano típico
                phone = '+51' + phone
            else:
                phone = '+51' + phone
        
        # Validar que tenga al menos 10 dígitos después del código de país
        if len(phone) >= 12:  # +51 + 9 dígitos mínimo
            return phone
        
        return None

    def get_configuration_summary(self):
        """Obtiene un resumen de la configuración de la regla"""
        config = {
            'type': self.get_alert_type_display(),
            'threshold': None,
            'recipients_count': self.recipients.count(),
            'categories_count': self.categories.count(),
            'products_count': self.products.count(),
        }
        
        if self.threshold_value:
            config['threshold'] = f"{self.threshold_value} unidades"
        elif self.threshold_percentage:
            config['threshold'] = f"{self.threshold_percentage}%"
        elif self.days_before_expiration:
            config['threshold'] = f"{self.days_before_expiration} días"
        elif self.accuracy_threshold:
            config['threshold'] = f"{self.accuracy_threshold}% precisión"
        
        return config


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
    
    ALERT_SOURCES = [
        ('rule', 'Regla configurada'),
        ('system', 'Sistema automático'),
        ('forecast', 'Módulo de predicciones'),
        ('manual', 'Creada manualmente'),
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
    source = models.CharField(
        max_length=20,
        choices=ALERT_SOURCES,
        default='rule',
        verbose_name="Origen"
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
    
    # Referencias a forecasting
    forecast_model = models.ForeignKey(
        'forecasting.ForecastModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name="Modelo de pronóstico relacionado"
    )
    demand_forecast = models.ForeignKey(
        'forecasting.DemandForecast',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name="Pronóstico relacionado"
    )
    reorder_recommendation = models.ForeignKey(
        'forecasting.ReorderRecommendation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name="Recomendación de reorden relacionada"
    )
    
    # Metadatos adicionales
    context_data = models.JSONField(default=dict, verbose_name="Datos de contexto")
    
    # Acciones recomendadas
    recommended_actions = models.JSONField(
        default=list,
        verbose_name="Acciones recomendadas",
        help_text="Lista de acciones que el usuario puede tomar"
    )
    
    # Prioridad calculada (basada en múltiples factores)
    priority_score = models.IntegerField(
        default=50,
        verbose_name="Puntuación de prioridad",
        help_text="Puntuación de 0-100 para ordenamiento"
    )
    
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
        ordering = ['-priority_score', '-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'severity']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['priority_score', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_severity_display()}"
    
    def save(self, *args, **kwargs):
        """Calcular priority_score automáticamente"""
        if not self.priority_score or self.priority_score == 50:
            self.priority_score = self.calculate_priority_score()
        super().save(*args, **kwargs)
    
    def calculate_priority_score(self):
        """Calcula la puntuación de prioridad basada en múltiples factores"""
        score = 50  # Base score
        
        # Factor de severidad (0-40 puntos)
        severity_scores = {
            'low': 10,
            'medium': 20,
            'high': 30,
            'critical': 40
        }
        score += severity_scores.get(self.severity, 20)
        
        # Factor de tiempo (0-20 puntos) - más reciente = mayor prioridad
        from django.utils import timezone
        
        # ✅ ARREGLO: Verificar si created_at existe antes de usarlo
        if self.created_at:
            hours_old = (timezone.now() - self.created_at).total_seconds() / 3600
            if hours_old < 1:
                score += 20
            elif hours_old < 6:
                score += 15
            elif hours_old < 24:
                score += 10
            elif hours_old < 72:
                score += 5
        else:
            # Si no hay created_at (alerta nueva), dar máxima prioridad de tiempo
            score += 20
        
        # Factor de producto (0-15 puntos)
        if self.product:
            current_stock = self.product.current_stock or 0
            if current_stock <= 0:
                score += 15  # Stock agotado
            elif current_stock <= (self.product.min_stock or 0):
                score += 10  # Stock bajo
        
        # Factor de demanda/forecasting (0-15 puntos)
        if self.rule and self.rule.alert_type in ['high_demand', 'demand_vs_stock', 'stockout_risk']:
            score += 15
        
        # Factor de contexto adicional (0-10 puntos)
        if self.context_data:
            if self.context_data.get('action_required'):
                score += 10
            elif self.context_data.get('days_until_expiry', float('inf')) <= 3:
                score += 8
        
        return min(100, max(0, score))
    
    def acknowledge(self, user):
        """Marcar alerta como reconocida"""
        if self.status == 'active':
            self.status = 'acknowledged'
            self.acknowledged_by = user
            self.acknowledged_at = timezone.now()
            self.save()
    
    def resolve(self, user):
        """Marcar alerta como resuelta"""
        if self.status in ['active', 'acknowledged']:
            self.status = 'resolved'
            self.resolved_by = user
            self.resolved_at = timezone.now()
            self.save()
    
    def dismiss(self, user):
        """Descartar alerta"""
        if self.status in ['active', 'acknowledged']:
            self.status = 'dismissed'
            self.resolved_by = user
            self.resolved_at = timezone.now()
            self.save()

    def get_whatsapp_message(self):
        """Genera mensaje optimizado para WhatsApp"""
        emoji_map = {
            'low': '⚠️',
            'medium': '🔸',
            'high': '🔴',
            'critical': '🚨'
        }
        
        emoji = emoji_map.get(self.severity, '📢')
        product_name = self.product.name if self.product else 'Sistema'
        
        message = f"{emoji} *DataLens Alerta*\n\n"
        message += f"*{self.title}*\n"
        
        if self.product:
            message += f"📦 Producto: {product_name}\n"
        
        if self.current_value is not None:
            message += f"📊 Valor actual: {self.current_value}\n"
        
        if self.threshold_value is not None:
            message += f"⚡ Umbral: {self.threshold_value}\n"
        
        # Información específica de forecasting
        if self.demand_forecast:
            message += f"📈 Demanda proyectada: {self.demand_forecast.predicted_demand}\n"
        
        if self.reorder_recommendation:
            message += f"📋 Recomendación: Ordenar {self.reorder_recommendation.recommended_quantity} unidades\n"
        
        message += f"📅 {self.created_at.strftime('%d/%m/%Y %H:%M')}\n"
        message += f"\n{self.message}"
        
        # Agregar acciones recomendadas si existen
        if self.recommended_actions:
            message += f"\n\n🎯 *Acciones recomendadas:*"
            for i, action in enumerate(self.recommended_actions[:3], 1):  # Máximo 3 acciones
                message += f"\n{i}. {action}"
        
        return message

    def get_recommended_actions_display(self):
        """Obtiene las acciones recomendadas como texto"""
        if not self.recommended_actions:
            return []
        
        # Mapeo de acciones comunes
        action_map = {
            'reorder_product': 'Realizar pedido de reabastecimiento',
            'adjust_stock': 'Ajustar niveles de stock',
            'check_inventory': 'Verificar inventario físico',
            'contact_supplier': 'Contactar proveedor',
            'update_forecast': 'Actualizar pronósticos',
            'review_demand': 'Revisar patrones de demanda',
            'remove_expired': 'Retirar productos vencidos',
            'stock_transfer': 'Transferir stock entre ubicaciones'
        }
        
        return [action_map.get(action, action) for action in self.recommended_actions]


class NotificationLog(models.Model):
    """Log de notificaciones enviadas"""
    
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
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
    
    # Metadatos adicionales para WhatsApp
    whatsapp_message_id = models.CharField(max_length=100, blank=True, verbose_name="ID mensaje WhatsApp")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Log de notificación"
        verbose_name_plural = "Logs de notificaciones"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient} - {self.status}"
