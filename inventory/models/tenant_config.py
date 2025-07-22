"""
Modelo para configuración de tenants con auto-provisioning
"""
from django.db import models
from django.core.exceptions import ValidationError
from authentication.models import Company
import uuid


class TenantConfig(models.Model):
    """
    Configuración de servicios externos para cada tenant/empresa
    Con auto-provisioning de WhatsApp Cloud y Gmail Zero-Touch
    """
    # ID único del tenant
    tenant_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name="Tenant ID"
    )
    
    # Relación con empresa
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='tenant_config',
        verbose_name="Empresa"
    )
    
    # Información del dominio
    domain = models.CharField(
        max_length=255,
        unique=True,
        default='example.com',
        verbose_name="Dominio"
    )
    email = models.EmailField(
        default='admin@example.com',
        verbose_name="Email principal"
    )
    whatsapp_display_name = models.CharField(
        max_length=100,
        default='Business Name',
        verbose_name="Nombre de WhatsApp Business"
    )
    
    # WhatsApp Cloud API (Meta)
    phone_number_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="WhatsApp Phone Number ID"
    )
    wa_token = models.TextField(
        blank=True,
        null=True,
        verbose_name="WhatsApp Access Token"
    )
    whatsapp_business_account_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="WhatsApp Business Account ID"
    )
    
    # Gmail Zero-Touch
    gsuite_key = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Service Account Key JSON"
    )
    dkim_selector = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="DKIM Selector"
    )
    dns_zone_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="DNS Zone ID"
    )
    
    # Verificación de dominio
    domain_verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Token de verificación de dominio"
    )
    domain_verified = models.BooleanField(
        default=False,
        verbose_name="Dominio verificado"
    )
    domain_verified_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de verificación del dominio"
    )
    
    # DNS Records
    spf_record = models.TextField(
        blank=True,
        null=True,
        verbose_name="SPF Record"
    )
    dkim_record = models.TextField(
        blank=True,
        null=True,
        verbose_name="DKIM Record"
    )
    dns_propagated = models.BooleanField(
        default=False,
        verbose_name="DNS propagado"
    )
    
    # Estado del tenant
    is_active = models.BooleanField(
        default=False,
        verbose_name="Tenant activo"
    )
    provisioning_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pendiente'),
            ('domain_verification', 'Verificando dominio'),
            ('whatsapp_provisioning', 'Provisionando WhatsApp'),
            ('gmail_provisioning', 'Provisionando Gmail'),
            ('dns_setup', 'Configurando DNS'),
            ('dns_propagation', 'Propagando DNS'),
            ('completed', 'Completado'),
            ('failed', 'Fallido'),
        ],
        default='pending',
        verbose_name="Estado de provisioning"
    )
    
    # Legacy fields (mantener compatibilidad)
    twilio_account_sid = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Twilio Account SID (Legacy)"
    )
    twilio_auth_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Twilio Auth Token (Legacy)"
    )
    whatsapp_from_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Número WhatsApp Business (Legacy)"
    )
    
    # OAuth2 para n8n
    oauth2_client_id = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        default='n8n-test-client-id',
        verbose_name="OAuth2 Client ID"
    )
    oauth2_client_secret = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        default='n8n-test-secret-123',
        verbose_name="OAuth2 Client Secret"
    )
    oauth2_token_url = models.URLField(
        blank=False,
        null=False,
        default='https://016e520d8ade.ngrok-free.app/oauth/token/',
        verbose_name="OAuth2 Token URL"
    )
    
    # N8N Configuration
    n8n_webhook_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL Webhook n8n"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Tenant"
        verbose_name_plural = "Configuraciones de Tenants"
        indexes = [
            models.Index(fields=['tenant_id']),
            models.Index(fields=['domain']),
            models.Index(fields=['provisioning_status']),
        ]
    
    def __str__(self):
        return f"Tenant: {self.domain} ({self.provisioning_status})"
    
    @property
    def is_whatsapp_active(self):
        """WhatsApp está activo si tiene phone_number_id y wa_token"""
        return bool(self.phone_number_id and self.wa_token)
    
    @property
    def is_gmail_active(self):
        """Gmail está activo si tiene gsuite_key y DNS propagado"""
        return bool(self.gsuite_key and self.dns_propagated)
    
    @property
    def is_configured(self):
        """Verificar si el tenant está completamente configurado"""
        return (
            self.domain_verified and
            self.is_active and
            self.provisioning_status == 'completed' and
            (self.is_whatsapp_active or self.is_gmail_active)
        )
    
    def clean(self):
        """Validaciones del modelo"""
        if self.domain and not self.domain.replace('-', '').replace('.', '').isalnum():
            raise ValidationError("Dominio contiene caracteres inválidos")
        
        if self.email and self.domain:
            email_domain = self.email.split('@')[1] if '@' in self.email else ''
            if email_domain != self.domain:
                raise ValidationError(f"Email debe pertenecer al dominio {self.domain}")


class TenantProvisioningLog(models.Model):
    """
    Logs del proceso de provisioning
    """
    tenant_config = models.ForeignKey(
        TenantConfig,
        on_delete=models.CASCADE,
        related_name='provisioning_logs'
    )
    step = models.CharField(
        max_length=100,
        verbose_name="Paso del provisioning"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('started', 'Iniciado'),
            ('success', 'Exitoso'),
            ('failed', 'Fallido'),
            ('retry', 'Reintentando'),
        ],
        verbose_name="Estado"
    )
    message = models.TextField(
        verbose_name="Mensaje"
    )
    error_details = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Detalles del error"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de Provisioning"
        verbose_name_plural = "Logs de Provisioning"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tenant_config.domain} - {self.step} - {self.status}"
