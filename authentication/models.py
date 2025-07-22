from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid
from django.utils import timezone
from cryptography.fernet import Fernet
import os
import json


class Company(models.Model):
    """Modelo para representar las empresas en el sistema"""
    name = models.CharField(max_length=200, verbose_name="Nombre de la empresa")
    ruc = models.CharField(max_length=11, unique=True, verbose_name="RUC")
    address = models.TextField(verbose_name="Dirección")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Email de contacto")
    industry = models.CharField(max_length=100, blank=True, verbose_name="Industria")
    website = models.URLField(blank=True, verbose_name="Sitio web")
    
    # ✅ NUEVO: Configuración WhatsApp simplificada
    whatsapp_business_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Número WhatsApp de Display",
        help_text="Número que verán los clientes (puede ser virtual)"
    )
    whatsapp_enabled = models.BooleanField(
        default=False,
        verbose_name="WhatsApp habilitado"
    )
    whatsapp_plan = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Básico - Número compartido'),
            ('premium', 'Premium - Número dedicado'),
            ('enterprise', 'Enterprise - API propia'),
        ],
        default='basic',
        verbose_name="Plan WhatsApp"
    )
    
    # Solo para clientes Enterprise que quieren su propia API
    # (La mayoría usará el servicio compartido)
    custom_whatsapp_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Configuración WhatsApp personalizada",
        help_text="Solo para plan Enterprise"
    )
    
    # Configuración del sistema
    max_users = models.PositiveIntegerField(default=5, verbose_name="Máximo de usuarios")
    subscription_type = models.CharField(
        max_length=20,
        choices=[
            ('trial', 'Prueba'),
            ('basic', 'Básico'),
            ('premium', 'Premium'),
        ],
        default='trial',
        verbose_name="Tipo de suscripción"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    is_active = models.BooleanField(default=True, verbose_name="Empresa activa")
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_whatsapp_display_info(self):
        """Obtener información de WhatsApp para mostrar en mensajes"""
        return {
            'company_name': self.name,
            'display_number': self.whatsapp_business_number or self.phone,
            'contact_email': self.email,
            'contact_phone': self.phone,
            'is_whatsapp_enabled': self.whatsapp_enabled,
            'plan': self.get_whatsapp_plan_display()
        }
    
    def assign_whatsapp_number_if_needed(self):
        """Asignar número de WhatsApp automáticamente si no tiene uno"""
        if not self.whatsapp_business_number and self.whatsapp_enabled:
            # Para plan básico, generar un número virtual o usar el teléfono
            if self.whatsapp_plan == 'basic':
                self.whatsapp_business_number = self.phone or f"+51999{self.id:06d}"
            self.save()
    
    def can_send_whatsapp(self):
        """Verificar si puede enviar mensajes de WhatsApp"""
        return self.whatsapp_enabled and self.is_active


class TenantConfig(models.Model):
    """Configuración de tenants para el flujo N8N"""
    tenant_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Nombre del tenant")
    domain = models.CharField(max_length=100, unique=True, verbose_name="Dominio")
    email_address = models.EmailField(verbose_name="Dirección de email")
    phone_number_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID del número de teléfono WhatsApp")
    wa_token = models.TextField(blank=True, null=True, verbose_name="Token de WhatsApp (encriptado)")
    gsuite_key = models.JSONField(default=dict, blank=True, verbose_name="Clave de G Suite (encriptado)")
    dkim_selector = models.CharField(max_length=50, blank=True, null=True, verbose_name="Selector DKIM")
    dns_zone_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID de zona DNS")
    is_active = models.BooleanField(default=False, verbose_name="Tenant activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    
    # Campo para autenticación N8N
    client_secret = models.CharField(
        max_length=128, 
        blank=True, 
        null=True, 
        verbose_name="Client Secret para N8N",
        help_text="Secret key para autenticación de APIs externas"
    )
    
    # Campos adicionales para el onboarding
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('domain_verified', 'Dominio verificado'),
            ('email_configured', 'Email configurado'),
            ('whatsapp_configured', 'WhatsApp configurado'),
            ('completed', 'Completado'),
            ('failed', 'Fallido'),
        ],
        default='pending',
        verbose_name="Estado de verificación"
    )
    
    class Meta:
        verbose_name = "Configuración de Tenant"
        verbose_name_plural = "Configuraciones de Tenant"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.domain})"
    
    def save(self, *args, **kwargs):
        """Generar client_secret automáticamente si no existe"""
        if not self.client_secret:
            import secrets
            self.client_secret = f"tenant_{secrets.token_urlsafe(32)}"
        super().save(*args, **kwargs)
    
    def encrypt_sensitive_data(self, data):
        """Encriptar datos sensibles"""
        if not data:
            return None
        key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Desencriptar datos sensibles"""
        if not encrypted_data:
            return None
        key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
        f = Fernet(key)
        return f.decrypt(encrypted_data.encode()).decode()
    
    def set_wa_token(self, token):
        """Establecer token de WhatsApp (encriptado)"""
        if token:
            self.wa_token = self.encrypt_sensitive_data(token)
    
    def get_wa_token(self):
        """Obtener token de WhatsApp (desencriptado)"""
        if self.wa_token:
            return self.decrypt_sensitive_data(self.wa_token)
        return None
    
    def set_gsuite_key(self, key_data):
        """Establecer clave de G Suite (encriptada)"""
        if key_data:
            key_json = json.dumps(key_data) if isinstance(key_data, dict) else key_data
            self.gsuite_key = {'encrypted': self.encrypt_sensitive_data(key_json)}
    
    def get_gsuite_key(self):
        """Obtener clave de G Suite (desencriptada)"""
        if self.gsuite_key and 'encrypted' in self.gsuite_key:
            decrypted = self.decrypt_sensitive_data(self.gsuite_key['encrypted'])
            return json.loads(decrypted) if decrypted else {}
        return self.gsuite_key


class UsageLog(models.Model):
    """Log de uso de servicios por tenant"""
    CHANNEL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('ocr', 'OCR'),
        ('ia', 'IA'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('success', 'Éxito'),
        ('failed', 'Fallido'),
        ('retry', 'Reintentando'),
    ]
    
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, related_name='usage_logs')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, verbose_name="Canal")
    action = models.CharField(max_length=100, verbose_name="Acción")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Timestamp")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Estado")
    details = models.JSONField(default=dict, blank=True, verbose_name="Detalles")
    
    # Campos adicionales para tracking
    request_id = models.UUIDField(default=uuid.uuid4, verbose_name="ID de solicitud")
    retry_count = models.PositiveIntegerField(default=0, verbose_name="Número de reintentos")
    error_message = models.TextField(blank=True, null=True, verbose_name="Mensaje de error")
    
    class Meta:
        verbose_name = "Log de Uso"
        verbose_name_plural = "Logs de Uso"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'channel', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.channel} - {self.action} ({self.status})"


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""
    
    def create_user(self, username, email=None, password=None, company=None, **extra_fields):
        """Crear un usuario regular"""
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        
        # Si no se proporciona empresa, crear una por defecto
        if not company:
            company, created = Company.objects.get_or_create(
                name='Empresa por Defecto',
                defaults={
                    'ruc': '00000000000',
                    'address': 'Dirección por defecto',
                    'email': 'admin@empresa.com',
                    'industry': 'General',
                    'subscription_type': 'premium',
                    'max_users': 100
                }
            )
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, company=company, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, company=None, **extra_fields):
        """Crear un superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superadmin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        
        # Para superusuarios, siempre crear/usar empresa por defecto si no se especifica
        if not company:
            company, created = Company.objects.get_or_create(
                name='Empresa por Defecto',
                defaults={
                    'ruc': '00000000000',
                    'address': 'Dirección por defecto',
                    'email': 'admin@empresa.com',
                    'industry': 'General',
                    'subscription_type': 'premium',
                    'max_users': 100
                }
            )
        
        return self.create_user(username, email, password, company, **extra_fields)


class User(AbstractUser):
    """Modelo de usuario personalizado"""
    
    ROLE_CHOICES = [
        ('superadmin', 'Super Administrador'),
        ('admin', 'Administrador'),
        ('analyst', 'Analista'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name="Empresa"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='analyst',
        verbose_name="Rol"
    )
    
    # Información adicional del usuario
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    position = models.CharField(max_length=100, blank=True, verbose_name="Cargo")
    department = models.CharField(max_length=100, blank=True, verbose_name="Departamento")
    
    # Configuraciones de notificaciones
    email_notifications = models.BooleanField(default=True, verbose_name="Notificaciones por email")
    whatsapp_notifications = models.BooleanField(default=False, verbose_name="Notificaciones por WhatsApp")
    dashboard_preferences = models.JSONField(default=dict, verbose_name="Preferencias del dashboard")
    
    # Metadatos
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Última IP de login")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    
    # Manager personalizado
    objects = UserManager()
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} - {self.company.name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def has_permission(self, permission):
        """Verificar si el usuario tiene un permiso específico"""
        role_permissions = {
            'superadmin': ['all'],
            'admin': ['manage_inventory', 'view_reports', 'manage_alerts', 'manage_users'],
            'analyst': ['view_reports', 'view_inventory'],
        }
        
        user_permissions = role_permissions.get(self.role, [])
        return 'all' in user_permissions or permission in user_permissions


class TenantCommunicationConfig(models.Model):
    """
    Configuración de comunicación por tenant - El cliente decide qué canal usar para cada evento
    """
    
    EVENT_CHOICES = [
        ('order_confirmed', 'Pedido Confirmado'),
        ('order_preparing', 'Pedido en Preparación'),
        ('order_ready', 'Pedido Listo'),
        ('order_delivered', 'Pedido Entregado'),
        ('order_cancelled', 'Pedido Cancelado'),
        ('payment_confirmed', 'Pago Confirmado'),
        ('payment_failed', 'Pago Fallido'),
        ('appointment_confirmed', 'Cita Confirmada'),
        ('appointment_reminder', 'Recordatorio de Cita'),
        ('service_completed', 'Servicio Completado'),
        ('promotional', 'Promocional'),
        ('support', 'Soporte'),
        ('inventory_low', 'Stock Bajo'),
        ('inventory_out', 'Sin Stock'),
        ('custom', 'Personalizado'),
    ]
    
    CHANNEL_CHOICES = [
        ('whatsapp_only', 'Solo WhatsApp'),
        ('email_only', 'Solo Email'),
        ('both_whatsapp_primary', 'Ambos (WhatsApp Principal)'),
        ('both_email_primary', 'Ambos (Email Principal)'),
        ('disabled', 'Deshabilitado'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, related_name='communication_configs')
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES, verbose_name="Tipo de Evento")
    channel_preference = models.CharField(max_length=30, choices=CHANNEL_CHOICES, verbose_name="Preferencia de Canal")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal', verbose_name="Prioridad")
    
    # Configuración de mensajes
    use_ai_personalization = models.BooleanField(default=True, verbose_name="Usar IA para personalizar")
    custom_message_template = models.TextField(blank=True, verbose_name="Plantilla personalizada")
    
    # Configuración de horarios
    send_immediately = models.BooleanField(default=True, verbose_name="Enviar inmediatamente")
    delay_minutes = models.PositiveIntegerField(default=0, verbose_name="Retraso en minutos")
    respect_business_hours = models.BooleanField(default=False, verbose_name="Respetar horario comercial")
    
    # Configuración avanzada
    max_retries = models.PositiveIntegerField(default=3, verbose_name="Máximo reintentos")
    fallback_channel = models.CharField(
        max_length=30, 
        choices=CHANNEL_CHOICES, 
        blank=True, 
        verbose_name="Canal de respaldo"
    )
    
    # Metadatos
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    
    class Meta:
        verbose_name = "Configuración de Comunicación"
        verbose_name_plural = "Configuraciones de Comunicación"
        unique_together = ['tenant', 'event_type']
        ordering = ['event_type']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.get_event_type_display()} - {self.get_channel_preference_display()}"
    
    def should_send_via_whatsapp(self):
        """Determinar si debe enviar por WhatsApp"""
        return self.channel_preference in ['whatsapp_only', 'both_whatsapp_primary', 'both_email_primary']
    
    def should_send_via_email(self):
        """Determinar si debe enviar por Email"""
        return self.channel_preference in ['email_only', 'both_whatsapp_primary', 'both_email_primary']
    
    def get_primary_channel(self):
        """Obtener el canal principal"""
        if 'whatsapp_primary' in self.channel_preference:
            return 'whatsapp'
        elif 'email_primary' in self.channel_preference:
            return 'email'
        elif self.channel_preference == 'whatsapp_only':
            return 'whatsapp'
        elif self.channel_preference == 'email_only':
            return 'email'
        return None


class TenantAIConfig(models.Model):
    """
    Configuración de IA por tenant - El cliente decide cómo usar la IA
    """
    
    AI_PROVIDER_CHOICES = [
        ('openai', 'OpenAI GPT'),
        ('claude', 'Claude'),
        ('gemini', 'Google Gemini'),
        ('custom', 'API Personalizada'),
        ('disabled', 'Deshabilitado'),
    ]
    
    TONE_CHOICES = [
        ('formal', 'Formal'),
        ('casual', 'Casual'),
        ('friendly', 'Amigable'),
        ('professional', 'Profesional'),
        ('enthusiastic', 'Entusiasta'),
        ('custom', 'Personalizado'),
    ]
    
    tenant = models.OneToOneField(TenantConfig, on_delete=models.CASCADE, related_name='ai_config')
    
    # Configuración del proveedor de IA
    ai_provider = models.CharField(
        max_length=20, 
        choices=AI_PROVIDER_CHOICES, 
        default='openai', 
        verbose_name="Proveedor de IA"
    )
    api_key_encrypted = models.TextField(blank=True, verbose_name="API Key (Encriptada)")
    custom_api_url = models.URLField(blank=True, verbose_name="URL API Personalizada")
    
    # Configuración de personalización
    default_tone = models.CharField(
        max_length=20, 
        choices=TONE_CHOICES, 
        default='friendly', 
        verbose_name="Tono por defecto"
    )
    brand_voice_description = models.TextField(
        blank=True, 
        verbose_name="Descripción de la voz de marca",
        help_text="Describe cómo debe sonar tu marca: profesional, cercana, técnica, etc."
    )
    custom_instructions = models.TextField(
        blank=True, 
        verbose_name="Instrucciones personalizadas",
        help_text="Instrucciones específicas para la IA sobre tu negocio"
    )
    
    # Configuración de uso
    max_tokens = models.PositiveIntegerField(default=150, verbose_name="Máximo tokens")
    temperature = models.FloatField(
        default=0.7, 
        verbose_name="Temperatura (0.0-1.0)",
        help_text="0.0 = Respuestas consistentes, 1.0 = Respuestas creativas"
    )
    include_customer_history = models.BooleanField(
        default=True, 
        verbose_name="Incluir historial del cliente"
    )
    include_product_info = models.BooleanField(
        default=True, 
        verbose_name="Incluir información de productos"
    )
    
    # Límites y controles
    daily_ai_limit = models.PositiveIntegerField(
        default=1000, 
        verbose_name="Límite diario de IA",
        help_text="Máximo número de mensajes con IA por día"
    )
    require_human_approval = models.BooleanField(
        default=False, 
        verbose_name="Requiere aprobación humana",
        help_text="Los mensajes de IA requieren aprobación antes de enviar"
    )
    
    # Metadatos
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    
    class Meta:
        verbose_name = "Configuración de IA"
        verbose_name_plural = "Configuraciones de IA"
    
    def __str__(self):
        return f"{self.tenant.name} - IA {self.get_ai_provider_display()}"
    
    def can_use_ai(self):
        """Verificar si puede usar IA"""
        return self.is_active and self.ai_provider != 'disabled'
