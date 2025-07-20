from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


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
